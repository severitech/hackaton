"""Webhook de Meta/WhatsApp: valida, responde 200 OK y procesa el mensaje."""

import hashlib
import hmac
import json
import logging
import threading

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

USE_CELERY = getattr(settings, "CELERY_BROKER_URL", "").startswith("redis")


@csrf_exempt
def webhook(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        return _verificar_webhook(request)
    if request.method == "POST":
        return _recibir_mensaje(request)
    return HttpResponse(status=405)


def _verificar_webhook(request: HttpRequest) -> HttpResponse:
    modo = request.GET.get("hub.mode")
    token = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")

    if modo == "subscribe" and token == settings.META_VERIFY_TOKEN:
        logger.info("Webhook de WhatsApp verificado correctamente.")
        return HttpResponse(challenge, content_type="text/plain")

    logger.warning("Verificación de webhook fallida. Token recibido: %s", token)
    return HttpResponse(status=403)


def _recibir_mensaje(request: HttpRequest) -> HttpResponse:
    if not _validar_firma(request):
        return HttpResponse(status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    for entrada in body.get("entry", []):
        for cambio in entrada.get("changes", []):
            valor = cambio.get("value", {})
            for msg in valor.get("messages", []):
                _despachar_mensaje(msg)

    # Meta exige 200 rápido
    return JsonResponse({"status": "ok"})


def _despachar_mensaje(msg: dict) -> None:
    meta_id = msg.get("id")
    numero = msg.get("from")
    tipo = msg.get("type")

    if not (meta_id and numero and tipo):
        return

    if tipo == "text":
        contenido = msg.get("text", {}).get("body", "")
    elif tipo == "audio":
        contenido = msg.get("audio", {}).get("id", "")
    else:
        logger.debug("Tipo de mensaje no soportado: %s", tipo)
        return

    if USE_CELERY:
        from .tasks import procesar_mensaje_entrante
        procesar_mensaje_entrante.delay(numero, meta_id, tipo, contenido)
    else:
        # Sin Redis: procesar en hilo separado para no bloquear la respuesta a Meta
        t = threading.Thread(
            target=_procesar_sincrono,
            args=(numero, meta_id, tipo, contenido),
            daemon=True,
        )
        t.start()


def _procesar_sincrono(numero: str, meta_id: str, tipo: str, contenido: str) -> None:
    """Procesamiento directo sin Celery (desarrollo / MVP sin Redis)."""
    from .procesador import procesar_mensaje
    try:
        procesar_mensaje(numero, meta_id, tipo, contenido)
    except Exception:
        logger.exception("Error procesando mensaje %s", meta_id)


def _validar_firma(request: HttpRequest) -> bool:
    app_secret = getattr(settings, "META_APP_SECRET", "")
    if not app_secret:
        return True

    firma_header = request.headers.get("X-Hub-Signature-256", "")
    if not firma_header.startswith("sha256="):
        return False

    firma_esperada = hmac.new(
        app_secret.encode(), request.body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(firma_header[7:], firma_esperada)
