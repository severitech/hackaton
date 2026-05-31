"""Servicio de integración con WhatsApp Cloud API de Meta."""

import logging
from typing import Optional

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v19.0"


class ServicioWhatsApp:
    def __init__(self):
        self.token: str = settings.META_WHATSAPP_TOKEN
        self.phone_id: str = settings.META_WHATSAPP_PHONE_NUMBER_ID
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def enviar_texto(self, numero: str, texto: str) -> dict:
        """Envía un mensaje de texto plano al número dado."""
        payload = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "text",
            "text": {"body": texto},
        }
        return self._post("messages", payload)

    def enviar_audio(self, numero: str, url_audio: str) -> dict:
        """Envía una nota de audio desde una URL pública."""
        payload = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "audio",
            "audio": {"link": url_audio},
        }
        return self._post("messages", payload)

    def descargar_media(self, media_id: str) -> bytes:
        """Descarga el contenido binario de un archivo multimedia de Meta."""
        with httpx.Client(timeout=30) as client:
            r = client.get(
                f"{WHATSAPP_API_URL}/{media_id}",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            r.raise_for_status()
            url = r.json().get("url")
            audio = client.get(url, headers={"Authorization": f"Bearer {self.token}"})
            audio.raise_for_status()
            return audio.content

    def _post(self, endpoint: str, payload: dict) -> dict:
        url = f"{WHATSAPP_API_URL}/{self.phone_id}/{endpoint}"
        with httpx.Client(timeout=30) as client:
            r = client.post(url, json=payload, headers=self.headers)
            r.raise_for_status()
            return r.json()
