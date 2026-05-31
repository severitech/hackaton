from django.urls import path

from .webhook import webhook

urlpatterns = [
    path("whatsapp/webhook/", webhook, name="whatsapp_webhook"),
]
