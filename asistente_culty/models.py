from django.db import models
from django.utils.translation import gettext_lazy as _


class EstadoConversacion(models.TextChoices):
    ESPERANDO_NOMBRE = "ESPERANDO_NOMBRE", _("Esperando nombre")
    ESPERANDO_UBICACION = "ESPERANDO_UBICACION", _("Esperando ubicación")
    ESPERANDO_CULTIVO_ANTERIOR = "ESPERANDO_CULTIVO_ANTERIOR", _("Esperando cultivo anterior")
    ESPERANDO_QUIMICOS = "ESPERANDO_QUIMICOS", _("Esperando agroquímicos")
    ESPERANDO_CULTIVO_OBJETIVO = "ESPERANDO_CULTIVO_OBJETIVO", _("Esperando cultivo objetivo")
    ESPERANDO_TAMANO_PARCELA = "ESPERANDO_TAMANO_PARCELA", _("Esperando tamaño parcela")
    ACTIVA = "ACTIVA", _("Activa")


class DireccionMensaje(models.TextChoices):
    ENTRANTE = "ENTRANTE", _("Entrante")
    SALIENTE = "SALIENTE", _("Saliente")


class TipoMensaje(models.TextChoices):
    TEXTO = "TEXTO", _("Texto")
    AUDIO = "AUDIO", _("Audio")


class PerfilAgricultor(models.Model):
    numero_whatsapp = models.CharField(max_length=20, unique=True, db_index=True)
    nombre = models.CharField(max_length=100, blank=True)
    municipio = models.CharField(max_length=100, blank=True)
    region = models.ForeignKey(
        "climate_intelligence.Region",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="agricultores",
    )
    cultivo_anterior = models.CharField(max_length=200, blank=True)
    agroquimicos_usados = models.TextField(blank=True)
    cultivo_objetivo = models.CharField(max_length=200, blank=True)
    tamano_parcela_ha = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    perfil_completo = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil Agricultor"
        verbose_name_plural = "Perfiles Agricultores"

    def __str__(self):
        return f"{self.nombre or 'Sin nombre'} ({self.numero_whatsapp})"


class SesionConversacion(models.Model):
    agricultor = models.ForeignKey(
        PerfilAgricultor, on_delete=models.CASCADE, related_name="sesiones"
    )
    estado = models.CharField(
        max_length=40,
        choices=EstadoConversacion.choices,
        default=EstadoConversacion.ESPERANDO_NOMBRE,
        db_index=True,
    )
    ultima_actividad = models.DateTimeField(auto_now=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sesión de Conversación"
        verbose_name_plural = "Sesiones de Conversación"
        ordering = ["-ultima_actividad"]

    def __str__(self):
        return f"Sesión {self.pk} — {self.agricultor} [{self.estado}]"


class Mensaje(models.Model):
    sesion = models.ForeignKey(
        SesionConversacion, on_delete=models.CASCADE, related_name="mensajes"
    )
    direccion = models.CharField(max_length=10, choices=DireccionMensaje.choices, db_index=True)
    tipo = models.CharField(max_length=10, choices=TipoMensaje.choices, default=TipoMensaje.TEXTO)
    texto_original = models.TextField(blank=True)
    texto_transcrito = models.TextField(blank=True)
    url_audio = models.URLField(blank=True)
    meta_message_id = models.CharField(max_length=100, unique=True, db_index=True, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mensaje"
        verbose_name_plural = "Mensajes"
        ordering = ["creado_en"]

    def __str__(self):
        return f"[{self.direccion}] {self.texto_original[:60]}"
