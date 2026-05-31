"""Servicio de transcripción de audio a texto (STT) vía Groq + Whisper."""

import logging
from abc import ABC, abstractmethod

from django.conf import settings

logger = logging.getLogger(__name__)


class BaseTranscripcion(ABC):
    @abstractmethod
    def transcribir(self, audio_bytes: bytes, nombre_archivo: str = "audio.ogg") -> str:
        ...


class TranscripcionGroqWhisper(BaseTranscripcion):
    """Transcripción usando Whisper large-v3 a través de la API de Groq."""

    def transcribir(self, audio_bytes: bytes, nombre_archivo: str = "audio.ogg") -> str:
        try:
            from groq import Groq  # type: ignore

            client = Groq(api_key=settings.GROQ_API_KEY)
            transcripcion = client.audio.transcriptions.create(
                file=(nombre_archivo, audio_bytes),
                model="whisper-large-v3",
                language="es",
                response_format="text",
            )
            return str(transcripcion).strip()
        except Exception as exc:
            logger.error("Error al transcribir audio con Groq: %s", exc)
            raise


class ServicioTranscripcion:
    """Fachada configurable para STT. Cambia de proveedor sin tocar la lógica."""

    def __init__(self, implementacion: BaseTranscripcion | None = None):
        self._impl = implementacion or TranscripcionGroqWhisper()

    def transcribir(self, audio_bytes: bytes, nombre_archivo: str = "audio.ogg") -> str:
        return self._impl.transcribir(audio_bytes, nombre_archivo)
