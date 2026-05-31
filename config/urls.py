"""
URL configuration for AgriTech climate intelligence platform.
"""

from django.contrib import admin
from django.urls import include, path
from climate_intelligence.api import api as climate_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', climate_api.urls),
    path('culty/', include('asistente_culty.urls')),
]
