# Achaich-AI-ru — AgriTech: Culty, Asistente Agrícola por WhatsApp

**Culty** es un asistente agrícola inteligente que opera por **WhatsApp**, diseñado para ayudar a agricultores del **Departamento de Santa Cruz, Bolivia**. Los agricultores pueden enviar mensajes de texto o notas de voz y recibir recomendaciones personalizadas basadas en su perfil y las condiciones climáticas actuales de su región.

El proyecto combina un **bot de WhatsApp conversacional** con un **backend de predicción climática** que anticipa anomalías severas (sequías e inundaciones) con hasta 12 meses de anticipación.

---

## Equipo

| Nombre | Rol |
|---|---|
| Jose Humberto Castro Ortiz | Desarrollador |
| Douglas Padilla Severiche | Desarrollador |
| Nicole Lozada Leon | Desarrolladora |

---

## Arquitectura General

```
Agricultor (WhatsApp)
        │
        ▼
Meta WhatsApp Cloud API
        │  webhook POST
        ▼
┌─────────────────────────────────────────┐
│           Django Backend                │
│                                         │
│  /culty/whatsapp/webhook/               │
│       │                                 │
│       ├── Texto  ──────────────────┐    │
│       └── Audio ──► Groq Whisper   │    │
│                     (STT)          │    │
│                         │          │    │
│                         ▼          │    │
│              Groq Llama 3.3-70b ◄──┘    │
│              + Perfil agricultor        │
│              + Predicción climática     │
│                         │               │
│                         ▼               │
│              Respuesta texto            │
│              + gTTS / Google TTS        │
└─────────────────────────────────────────┘
        │
        ▼
Meta WhatsApp Cloud API
        │
        ▼
Agricultor recibe texto + audio
```

---

## Componentes Principales

### 1. Asistente Culty (`asistente_culty/`)

Bot conversacional de WhatsApp para agricultores.

**Flujo de onboarding:** Al escribir por primera vez, Culty hace 6 preguntas para armar el perfil del agricultor:
1. Nombre
2. Municipio / zona
3. Cultivo de la última campaña
4. Agroquímicos e insumos usados
5. Cultivo que quiere sembrar
6. Tamaño de parcela (hectáreas)

Una vez completado el perfil, el agricultor puede hacer preguntas libremente sobre su campo.

**Tipos de mensaje soportados:**
- Texto: procesado directamente por el LLM
- Audio: transcrito primero con Groq Whisper (STT), luego procesado por el LLM

**Respuesta:** siempre se envía texto; si el TTS está configurado, también se envía una nota de audio.

### 2. Inteligencia Climática (`climate_intelligence/`)

API REST para predicciones climáticas de las 5 regiones agrícolas de Santa Cruz:
- Norte Integrado
- Chiquitania
- Chaco Cruceño
- Valles Cruceños
- Pantanal

Predice anomalías de tipo `SEQUIA`, `INUNDACION` o `NORMAL` con nivel de severidad (1-5) y confianza (0-1), conectando con Google Vertex AI en producción o usando un simulador realista en desarrollo.

---

## Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Framework web | Django 5.0 + Django-Ninja |
| Base de datos | PostgreSQL |
| Procesamiento async | Celery + Redis |
| WhatsApp API | Meta WhatsApp Cloud API v19 |
| STT (voz a texto) | Groq Whisper |
| LLM | Groq Llama 3.3-70b-versatile |
| TTS (texto a voz) | gTTS (dev) / Google Cloud TTS (prod) |
| Predicciones climáticas | Google Vertex AI |
| Datos satelitales | Google Earth Engine |
| Alertas en lenguaje natural | Google Gemini 1.5 Flash |
| Datos climáticos históricos | Open-Meteo API |
| Servidor de producción | Gunicorn + Uvicorn |
| Contenedores | Docker + Docker Compose |
| Deploy | Google Cloud Run |

---

## Estructura del Proyecto

```
hackaton/
│
├── asistente_culty/                # Bot de WhatsApp (Culty)
│   ├── models.py                   # PerfilAgricultor, SesionConversacion, Mensaje
│   ├── webhook.py                  # Endpoint del webhook Meta/WhatsApp
│   ├── procesador.py               # Lógica central de procesamiento de mensajes
│   ├── conversacion.py             # Máquina de estados del onboarding
│   ├── tasks.py                    # Tareas Celery para procesamiento async
│   ├── urls.py                     # Rutas del módulo
│   └── services/
│       ├── whatsapp.py             # Cliente WhatsApp Cloud API
│       ├── asistente_ia.py         # Integración Groq/Llama (LLM)
│       ├── voz_a_texto.py          # Transcripción con Groq Whisper
│       └── texto_a_voz.py          # Síntesis de voz gTTS / Google TTS
│
├── climate_intelligence/           # Predicciones climáticas
│   ├── models.py                   # Region, ClimatePrediction
│   ├── api.py                      # Endpoints REST (Django-Ninja)
│   ├── admin.py                    # Panel de administración + dashboard
│   └── services/
│       ├── vertex_ai.py            # Integración Google Vertex AI (real/mock)
│       ├── gemini_service.py       # Alertas con Google Gemini
│       ├── climate_data.py         # Datos Open-Meteo
│       └── earth_engine.py         # Datos satelitales Google Earth Engine
│
├── config/                         # Configuración central de Django
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
│
├── telegram_bot/                   # Bot alternativo para Telegram (experimental)
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── requirements.txt
└── .env.example
```

---

## Configuración y Puesta en Marcha

### 1. Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto basándote en `.env.example`:

```bash
cp .env.example .env
```

Variables obligatorias para el bot de WhatsApp:

```env
# Django
SECRET_KEY=tu-clave-secreta
DEBUG=True

# Base de datos
DATABASE_URL=postgres://postgres:postgres@db:5432/agritech

# WhatsApp Cloud API (Meta)
META_WHATSAPP_TOKEN=tu-token-de-acceso
META_WHATSAPP_PHONE_NUMBER_ID=tu-phone-number-id
META_VERIFY_TOKEN=un-token-que-elijas-vos
META_APP_SECRET=tu-app-secret

# Groq (STT + LLM)
GROQ_API_KEY=tu-clave-groq
GROQ_LLM_MODEL=llama-3.3-70b-versatile

# Redis (para Celery)
CELERY_BROKER_URL=redis://redis:6379/0
```

### 2. Levantar con Docker Compose

```bash
docker-compose up --build
```

Esto levanta Django (puerto `8000`), PostgreSQL y Redis.

### 3. Aplicar Migraciones y Crear Superusuario

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### 4. Poblar Datos Climáticos

```bash
docker-compose exec web python manage.py seed_climate_data
```

### 5. Levantar Worker de Celery

```bash
docker-compose exec web celery -A config worker -l info
```

Sin Redis/Celery, los mensajes se procesan en hilos separados (modo desarrollo).

---

## Configurar el Webhook de WhatsApp

1. Desplegá el backend con HTTPS (Cloud Run en producción, o [ngrok](https://ngrok.com/) para desarrollo local).
2. En [Meta for Developers](https://developers.facebook.com/apps) → tu App → WhatsApp → Configuración:
   - **URL del webhook:** `https://<tu-dominio>/culty/whatsapp/webhook/`
   - **Token de verificación:** el valor de `META_VERIFY_TOKEN`
   - **Evento suscrito:** `messages`
3. Completá `META_WHATSAPP_TOKEN` con el token de acceso permanente.
4. Completá `META_WHATSAPP_PHONE_NUMBER_ID` con el ID del número de WhatsApp.

---

## API Endpoints (Climate Intelligence)

Documentación interactiva disponible en `/api/docs` (Swagger/OpenAPI).

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/health` | Estado del servicio |
| GET | `/api/regions` | Lista las 5 regiones agrícolas |
| GET | `/api/predictions/{id}` | Predicciones de una región |
| GET | `/api/predictions/{id}/timeline` | Línea temporal para gráficos |
| GET | `/api/dashboard/summary` | Resumen global de anomalías |
| GET | `/api/regions/{id}/risk-assessment` | Evaluación de riesgo compuesto (0-10) |

---

## Deploy en Google Cloud Run

El `Dockerfile` y `entrypoint.sh` están optimizados para Cloud Run:

- Ejecuta la app bajo un usuario no privilegiado (`appuser`)
- Sirve estáticos con **WhiteNoise** (sin Nginx separado)
- Espera a que PostgreSQL esté disponible antes de aplicar migraciones
- Inicia con **Gunicorn + Uvicorn workers** para manejo concurrente

```bash
# Construir y subir imagen a Google Artifact Registry
gcloud builds submit --tag gcr.io/<PROJECT_ID>/agritech-backend

# Desplegar en Cloud Run
gcloud run deploy agritech-backend \
  --image gcr.io/<PROJECT_ID>/agritech-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Interfaces de Administración

- **Documentación API:** `http://localhost:8000/api/docs`
- **Panel de administración Django:** `http://localhost:8000/admin/`
- **Dashboard climático:** `http://localhost:8000/admin/climate-dashboard/`
