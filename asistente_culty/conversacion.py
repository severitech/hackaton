"""Máquina de estados para el onboarding conversacional del agricultor."""

import logging
from typing import Optional

from .models import EstadoConversacion, PerfilAgricultor, SesionConversacion

logger = logging.getLogger(__name__)

PREGUNTAS = {
    EstadoConversacion.ESPERANDO_NOMBRE: "¡Hola! Soy Culty, tu asistente del campo 🌱. ¿Cómo te llamás?",
    EstadoConversacion.ESPERANDO_UBICACION: "¿De qué municipio o zona sos? (por ejemplo: San Julián, Pailón, Cuatro Cañadas...)",
    EstadoConversacion.ESPERANDO_CULTIVO_ANTERIOR: "¿Qué sembraste en la última campaña?",
    EstadoConversacion.ESPERANDO_QUIMICOS: "¿Qué agroquímicos o insumos usaste en esa campaña? Si no usaste nada, decime 'ninguno'.",
    EstadoConversacion.ESPERANDO_CULTIVO_OBJETIVO: "¿Qué pensás sembrar ahora?",
    EstadoConversacion.ESPERANDO_TAMANO_PARCELA: "¿Cuántas hectáreas tiene tu parcela aproximadamente?",
}

TRANSICIONES = {
    EstadoConversacion.ESPERANDO_NOMBRE: EstadoConversacion.ESPERANDO_UBICACION,
    EstadoConversacion.ESPERANDO_UBICACION: EstadoConversacion.ESPERANDO_CULTIVO_ANTERIOR,
    EstadoConversacion.ESPERANDO_CULTIVO_ANTERIOR: EstadoConversacion.ESPERANDO_QUIMICOS,
    EstadoConversacion.ESPERANDO_QUIMICOS: EstadoConversacion.ESPERANDO_CULTIVO_OBJETIVO,
    EstadoConversacion.ESPERANDO_CULTIVO_OBJETIVO: EstadoConversacion.ESPERANDO_TAMANO_PARCELA,
    EstadoConversacion.ESPERANDO_TAMANO_PARCELA: EstadoConversacion.ACTIVA,
}


def obtener_o_crear_sesion(agricultor: PerfilAgricultor) -> SesionConversacion:
    sesion = agricultor.sesiones.order_by("-ultima_actividad").first()
    if not sesion:
        estado_inicial = (
            EstadoConversacion.ACTIVA
            if agricultor.perfil_completo
            else _primer_estado_pendiente(agricultor)
        )
        sesion = SesionConversacion.objects.create(agricultor=agricultor, estado=estado_inicial)
    return sesion


def procesar_respuesta_onboarding(sesion: SesionConversacion, texto: str) -> Optional[str]:
    """
    Guarda el dato recibido en el perfil y avanza el estado.
    Retorna la siguiente pregunta o None si el perfil ya está completo.
    """
    agricultor = sesion.agricultor
    estado = sesion.estado

    if estado == EstadoConversacion.ESPERANDO_NOMBRE:
        agricultor.nombre = texto.strip().title()
    elif estado == EstadoConversacion.ESPERANDO_UBICACION:
        agricultor.municipio = texto.strip().title()
        _intentar_vincular_region(agricultor)
    elif estado == EstadoConversacion.ESPERANDO_CULTIVO_ANTERIOR:
        agricultor.cultivo_anterior = texto.strip()
    elif estado == EstadoConversacion.ESPERANDO_QUIMICOS:
        agricultor.agroquimicos_usados = texto.strip()
    elif estado == EstadoConversacion.ESPERANDO_CULTIVO_OBJETIVO:
        agricultor.cultivo_objetivo = texto.strip()
    elif estado == EstadoConversacion.ESPERANDO_TAMANO_PARCELA:
        try:
            agricultor.tamano_parcela_ha = float(texto.replace(",", ".").split()[0])
        except (ValueError, IndexError):
            agricultor.tamano_parcela_ha = None

    agricultor.save()

    siguiente = TRANSICIONES.get(estado)
    if siguiente:
        sesion.estado = siguiente
        sesion.save(update_fields=["estado"])

    if sesion.estado == EstadoConversacion.ACTIVA:
        agricultor.perfil_completo = True
        agricultor.save(update_fields=["perfil_completo"])
        return (
            f"¡Perfecto, {agricultor.nombre}! Ya tengo todo lo que necesito. "
            "Ahora podés preguntarme lo que quieras sobre tu campo 🌾"
        )

    return PREGUNTAS.get(sesion.estado)


def siguiente_pregunta_pendiente(sesion: SesionConversacion) -> Optional[str]:
    """Retorna la pregunta correspondiente al estado actual si aún es onboarding."""
    if sesion.estado == EstadoConversacion.ACTIVA:
        return None
    return PREGUNTAS.get(sesion.estado)


def _primer_estado_pendiente(agricultor: PerfilAgricultor) -> str:
    if not agricultor.nombre:
        return EstadoConversacion.ESPERANDO_NOMBRE
    if not agricultor.municipio:
        return EstadoConversacion.ESPERANDO_UBICACION
    if not agricultor.cultivo_anterior:
        return EstadoConversacion.ESPERANDO_CULTIVO_ANTERIOR
    if not agricultor.agroquimicos_usados:
        return EstadoConversacion.ESPERANDO_QUIMICOS
    if not agricultor.cultivo_objetivo:
        return EstadoConversacion.ESPERANDO_CULTIVO_OBJETIVO
    if not agricultor.tamano_parcela_ha:
        return EstadoConversacion.ESPERANDO_TAMANO_PARCELA
    return EstadoConversacion.ACTIVA


def _intentar_vincular_region(agricultor: PerfilAgricultor) -> None:
    try:
        from climate_intelligence.models import Region

        municipio_lower = agricultor.municipio.lower()
        for region in Region.objects.all():
            if municipio_lower in region.nombre.lower() or region.nombre.lower() in municipio_lower:
                agricultor.region = region
                return
    except Exception:
        pass
