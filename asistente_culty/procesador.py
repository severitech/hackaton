"""Lógica central de procesamiento de mensajes (reutilizable con o sin Celery)."""

import logging

from .models import DireccionMensaje, EstadoConversacion, Mensaje, PerfilAgricultor, TipoMensaje
from .conversacion import obtener_o_crear_sesion, procesar_respuesta_onboarding
from .services.whatsapp import ServicioWhatsApp
from .services.texto_a_voz import ServicioSintesisVoz
from .services.asistente_ia import ServicioAsistente

logger = logging.getLogger(__name__)


def procesar_mensaje(numero: str, meta_id: str, tipo: str, contenido: str) -> None:
    # Idempotencia
    if Mensaje.objects.filter(meta_message_id=meta_id).exists():
        logger.info("Mensaje %s ya procesado, ignorando.", meta_id)
        return

    agricultor, _ = PerfilAgricultor.objects.get_or_create(numero_whatsapp=numero)
    sesion = obtener_o_crear_sesion(agricultor)

    texto_usuario = contenido
    if tipo == "audio":
        texto_usuario = _transcribir(contenido)

    Mensaje.objects.create(
        sesion=sesion,
        direccion=DireccionMensaje.ENTRANTE,
        tipo=TipoMensaje.AUDIO if tipo == "audio" else TipoMensaje.TEXTO,
        texto_original=contenido if tipo == "text" else "",
        texto_transcrito=texto_usuario,
        meta_message_id=meta_id,
    )

    if sesion.estado != EstadoConversacion.ACTIVA:
        respuesta = procesar_respuesta_onboarding(sesion, texto_usuario)
    else:
        respuesta = _consultar_ia(agricultor, sesion, texto_usuario)

    if not respuesta:
        return

    _enviar_respuesta(numero, respuesta, sesion)


def _enviar_respuesta(numero: str, texto: str, sesion) -> None:
    wa = ServicioWhatsApp()
    wa.enviar_texto(numero, texto)

    try:
        tts = ServicioSintesisVoz()
        audio_bytes = tts.sintetizar(texto)
        url = _subir_audio(audio_bytes)
        if url:
            wa.enviar_audio(numero, url)
    except Exception as exc:
        logger.warning("TTS falló, solo se envió texto: %s", exc)

    Mensaje.objects.create(
        sesion=sesion,
        direccion=DireccionMensaje.SALIENTE,
        tipo=TipoMensaje.TEXTO,
        texto_original=texto,
    )


def _transcribir(media_id: str) -> str:
    from .services.voz_a_texto import ServicioTranscripcion
    wa = ServicioWhatsApp()
    audio_bytes = wa.descargar_media(media_id)
    return ServicioTranscripcion().transcribir(audio_bytes, "audio.ogg")


def _consultar_ia(agricultor: PerfilAgricultor, sesion, texto: str) -> str:
    perfil = {
        "nombre": agricultor.nombre,
        "municipio": agricultor.municipio,
        "cultivo_anterior": agricultor.cultivo_anterior,
        "agroquimicos_usados": agricultor.agroquimicos_usados,
        "cultivo_objetivo": agricultor.cultivo_objetivo,
        "tamano_parcela_ha": str(agricultor.tamano_parcela_ha or ""),
    }

    clima = None
    if agricultor.region_id:
        try:
            from climate_intelligence.models import ClimatePrediction
            pred = ClimatePrediction.objects.filter(
                region=agricultor.region
            ).order_by("-fecha_prediccion").first()
            if pred:
                clima = {
                    "Tipo de anomalía": pred.tipo_anomalia,
                    "Severidad": pred.severidad,
                    "Confianza": f"{pred.confianza * 100:.0f}%",
                }
        except Exception:
            pass

    historial = list(
        sesion.mensajes.order_by("-creado_en")[:6].values("direccion", "texto_transcrito", "texto_original")
    )
    historial_fmt = [
        {
            "role": "user" if m["direccion"] == DireccionMensaje.ENTRANTE else "assistant",
            "content": m["texto_transcrito"] or m["texto_original"],
        }
        for m in reversed(historial)
    ]

    return ServicioAsistente().responder(texto, perfil, clima, historial_fmt)


def _subir_audio(audio_bytes: bytes) -> str | None:
    # En producción: subir a GCS y retornar URL pública
    return None
