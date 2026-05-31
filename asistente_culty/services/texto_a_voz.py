"""Servicio de síntesis de voz (TTS) en español para WhatsApp."""

import logging
import os
import tempfile
from abc import ABC, abstractmethod

from django.conf import settings

logger = logging.getLogger(__name__)


class BaseSintesisVoz(ABC):
    @abstractmethod
    def sintetizar(self, texto: str) -> bytes:
        """Devuelve bytes de audio MP3/OGG en español."""
        ...


class SintesisVozGTTS(BaseSintesisVoz):
    """TTS gratuito con gTTS (MVP). Reemplazar por Google Cloud TTS en producción."""

    def sintetizar(self, texto: str) -> bytes:
        try:
            from gtts import gTTS  # type: ignore

            tts = gTTS(text=texto, lang="es", slow=False)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tts.save(tmp.name)
                tmp_path = tmp.name
            with open(tmp_path, "rb") as f:
                data = f.read()
            os.unlink(tmp_path)
            return data
        except Exception as exc:
            logger.error("Error en gTTS: %s", exc)
            raise


class SintesisVozGoogleCloud(BaseSintesisVoz):
    """TTS de alta calidad con Google Cloud Text-to-Speech."""

    def sintetizar(self, texto: str) -> bytes:
        try:
            from google.cloud import texttospeech  # type: ignore

            client = texttospeech.TextToSpeechClient()
            synthesis_input = texttospeech.SynthesisInput(text=texto)
            voice = texttospeech.VoiceSelectionParams(
                language_code="es-US",
                name="es-US-Neural2-B",
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            return response.audio_content
        except Exception as exc:
            logger.error("Error en Google Cloud TTS: %s", exc)
            raise


class ServicioSintesisVoz:
    """Fachada configurable para TTS."""

    def __init__(self, implementacion: BaseSintesisVoz | None = None):
        usar_google = getattr(settings, "TTS_PROVEEDOR", "gtts") == "google"
        self._impl = implementacion or (
            SintesisVozGoogleCloud() if usar_google else SintesisVozGTTS()
        )

    def sintetizar(self, texto: str) -> bytes:
        return self._impl.sintetizar(texto)
