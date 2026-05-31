"""Servicio LLM: arma el contexto del agricultor + clima y consulta Groq/Llama."""

import logging
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Eres Culty, un asistente agrícola amigable que ayuda a agricultores de Santa Cruz, Bolivia.
Respondes siempre en español, con un tono cálido, simple y cercano (lenguaje de campo, no técnico).
Tus respuestas son concretas, accionables y breves (máximo 4 oraciones).
Cuando des recomendaciones, basalas en los datos de clima y el perfil del agricultor que se te proporcionan."""


class ServicioAsistente:
    def __init__(self):
        self.api_key: str = settings.GROQ_API_KEY
        self.modelo: str = getattr(settings, "GROQ_LLM_MODEL", "llama-3.3-70b-versatile")

    def responder(
        self,
        mensaje_usuario: str,
        perfil: dict,
        clima: Optional[dict] = None,
        historial: Optional[list[dict]] = None,
    ) -> str:
        """Genera respuesta del LLM con contexto completo del agricultor."""
        try:
            from groq import Groq  # type: ignore

            client = Groq(api_key=self.api_key)

            contexto_perfil = self._armar_contexto_perfil(perfil, clima)
            mensajes = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n" + contexto_perfil}]

            if historial:
                mensajes.extend(historial[-6:])  # últimos 3 turnos

            mensajes.append({"role": "user", "content": mensaje_usuario})

            respuesta = client.chat.completions.create(
                model=self.modelo,
                messages=mensajes,
                max_tokens=300,
                temperature=0.7,
            )
            return respuesta.choices[0].message.content.strip()
        except Exception as exc:
            logger.error("Error al consultar LLM: %s", exc)
            return "Disculpá, tuve un problemita. ¿Podés repetir tu pregunta?"

    def _armar_contexto_perfil(self, perfil: dict, clima: Optional[dict]) -> str:
        lineas = ["=== PERFIL DEL AGRICULTOR ==="]
        if perfil.get("nombre"):
            lineas.append(f"Nombre: {perfil['nombre']}")
        if perfil.get("municipio"):
            lineas.append(f"Municipio: {perfil['municipio']}")
        if perfil.get("cultivo_anterior"):
            lineas.append(f"Cultivo anterior: {perfil['cultivo_anterior']}")
        if perfil.get("agroquimicos_usados"):
            lineas.append(f"Agroquímicos usados: {perfil['agroquimicos_usados']}")
        if perfil.get("cultivo_objetivo"):
            lineas.append(f"Cultivo que quiere sembrar: {perfil['cultivo_objetivo']}")
        if perfil.get("tamano_parcela_ha"):
            lineas.append(f"Tamaño parcela: {perfil['tamano_parcela_ha']} ha")

        if clima:
            lineas.append("\n=== CONDICIONES CLIMÁTICAS ACTUALES ===")
            for k, v in clima.items():
                lineas.append(f"{k}: {v}")

        return "\n".join(lineas)
