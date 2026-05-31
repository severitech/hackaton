"""Tareas Celery (usadas solo cuando Redis está disponible)."""

from celery import shared_task
from .procesador import procesar_mensaje


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def procesar_mensaje_entrante(self, numero: str, meta_id: str, tipo: str, contenido: str):
    try:
        procesar_mensaje(numero, meta_id, tipo, contenido)
    except Exception as exc:
        raise self.retry(exc=exc)
