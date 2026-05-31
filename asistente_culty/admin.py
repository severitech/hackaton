from django.contrib import admin

from .models import Mensaje, PerfilAgricultor, SesionConversacion


@admin.register(PerfilAgricultor)
class PerfilAgricultorAdmin(admin.ModelAdmin):
    list_display = ["numero_whatsapp", "nombre", "municipio", "cultivo_objetivo", "perfil_completo", "actualizado_en"]
    list_filter = ["perfil_completo", "region"]
    search_fields = ["numero_whatsapp", "nombre", "municipio"]
    readonly_fields = ["creado_en", "actualizado_en"]


@admin.register(SesionConversacion)
class SesionConversacionAdmin(admin.ModelAdmin):
    list_display = ["pk", "agricultor", "estado", "ultima_actividad"]
    list_filter = ["estado"]
    search_fields = ["agricultor__nombre", "agricultor__numero_whatsapp"]


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ["pk", "sesion", "direccion", "tipo", "texto_original", "creado_en"]
    list_filter = ["direccion", "tipo"]
    search_fields = ["texto_original", "texto_transcrito", "meta_message_id"]
    readonly_fields = ["creado_en"]
