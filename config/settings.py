import os
import ssl
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-dev-key")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    # Local apps
    "accounts",
    "chat",
    "core",
    "documents",
    "retrieval",
    "notes",
    "flashcards",
    "memory",
    "tasks"
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', 
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.RequestLoggingMiddleware',

]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = "config.asgi.application"

import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,  # Keeps connections alive for 10 minutes to boost speed
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    # Only applied to views that explicitly opt in via throttle_classes + throttle_scope (ChatStreamView, accounts.views.LoginView) - not a DEFAULT_THROTTLE_CLASSES applying everywhere, since most endpoints here have no real cost/abuse concern that justifies it.
    "DEFAULT_THROTTLE_RATES": {
        "chat": os.getenv("RATELIMIT_CHAT_RATE", "30/m"),
        "login": os.getenv("RATELIMIT_LOGIN_RATE", "10/m"),
    },
}


# Cache (Redis)
# Used by django-ratelimit (and optionally for future caching needs).
# Using a distinct Redis DB (db=1) from Celery's broker (db=0) so the two concerns don't share a namespace and a cache flush can't accidentally drain the task queue.
# DRF's throttling (see REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] above) reads from the "default" cache alias automatically - no extra setting needed beyond this.
# Django automatically adds a ':1:' prefix to all its cache keys behind the scenes. This namespace isolation keeps your cache completely safe from interfering with Celery.
# NOTE: Django's native RedisCache backend automatically detects the connection protocol.
# If REDIS_CACHE_URL starts with 'rediss://', Django's underlying client (redis-py) automatically handles the SSL/TLS cryptographic handshake and certificate verification out of the box without requiring extra transport option dictionaries.
REDIS_CACHE_URL = os.getenv("REDIS_CACHE_URL", "redis://localhost:6379/1")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_CACHE_URL,
    }
}

 
SPECTACULAR_SETTINGS = {
    "TITLE": "Knowledge Assistant API",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,

}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=100),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}
 
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8501").split(",")



#  Chat 
# Caps how many past messages are replayed to the model on each turn, so prompt size (latency + token cost) stays bounded as a conversation grows.
CHAT_HISTORY_MAX_MESSAGES = int(os.getenv("CHAT_HISTORY_MAX_MESSAGES", "20"))

# Documents:
# Local disk for now (Django's default FileSystemStorage). Swapping to
# S3/MinIO later only means changing DEFAULT_FILE_STORAGE + credentials -
# nothing in documents/models.py or views.py needs to change, since they
# only ever call `file.open()` / `file.delete()`, never touch paths directly.

# Absolute path to the directory that will hold user-uploaded files
MEDIA_ROOT = BASE_DIR / "media"
# URL that handles the media served from MEDIA_ROOT
MEDIA_URL = "/media/"
# Caps the size of the files allowed to be uploaded
DOCUMENT_MAX_UPLOAD_SIZE_MB = int(os.getenv("DOCUMENT_MAX_UPLOAD_SIZE_MB", "60"))


# Retrieval (RAG) 
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR") or str(BASE_DIR / "chroma_data")
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "4"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))

# Tavily search Agent tool
# Web search is optional - only included in the agent's tool list if a key is actually configured
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
WEB_SEARCH_MAX_RESULTS = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "3"))

# workspace-search
RESULTS_PER_SOURCE = int(os.getenv("RESULTS_PER_SOURCE","10"))


# Celery & Redis setup
# Redis is used purely as the message broker (+ result backend for debugging) for now - task status that the app actually queries lives in our own models (ContentIndex, FlashcardSet), not Celery's result backend.
# Caching uses of Redis later
CELERY_REDIS_URL = os.getenv("CELERY_REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = CELERY_REDIS_URL
CELERY_RESULT_BACKEND = CELERY_REDIS_URL

# Only enforce strict SSL connection details if using a remote secured Redis instance (rediss://)
if CELERY_REDIS_URL.startswith("rediss://"):
    # Clean injection directly into the URL parameters
    CELERY_BROKER_URL = f"{CELERY_REDIS_URL}?ssl_cert_reqs=CERT_REQUIRED"
    CELERY_RESULT_BACKEND = f"{CELERY_REDIS_URL}?ssl_cert_reqs=CERT_REQUIRED"

else:
    CELERY_BROKER_TRANSPORT_OPTIONS = {}
    CELERY_REDIS_BACKEND_TRANSPORT_OPTIONS = {}

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE


# LangSmith
# Unlike GROQ_API_KEY or TAVILY_API_KEY, LangSmith settings are NOT read
# through Django settings. LangChain reads LANGSMITH_TRACING,
# LANGSMITH_API_KEY, and LANGSMITH_PROJECT directly from environment
# variables when it is imported.
#
# Since load_dotenv() has already loaded the .env file into os.environ
# before any LangChain code runs, tracing is enabled automatically for
# model calls, agent tool calls, and retrieval calls. No extra Django
# settings or code are required.
#
# Adding LANGSMITH_API_KEY to Django settings would have no effect because
# nothing reads it. See .env.example for the required environment
# variables.


# Logging
# JSON to stdout (captured by whatever process manager/Docker/systemd runs this in production) plus a rotating file, so logs survive a container restart during local development. No custom dashboard here on purpose - LangSmith will covers LLM-specific tracing in far more depth than a hand-built UI would, and Django admin already lets you inspect ContentIndex/FlashcardSet/etc. status directly.
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
 
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "core.logging.JSONFormatter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "app.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10MB  - if bigger new log-file created
            "backupCount": 5, #When a sixth rotation happens-oldest deleted.
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        # Django's own request logger would otherwise double-log every request in its own (non-JSON) format alongside our middleware.
        "django.server": {"handlers": ["console", "file"], "level": "WARNING", "propagate": False},
        # "core.request": {"level": "INFO",},
        # "tools": {"level": "INFO",},
        # "chat": {"level": "INFO",},
    },
}

# Logging hierarchy (simplified)
#
# root
# ├── django
# │   ├── django.server
# │   ├── django.request
# │   ├── django.db.backends
# │   ├── django.security
# │   └── django.template
# │
# ├── core.request
# ├── chat
# ├── tools
# └── embedding
#
# Loggers inherit settings from their parent unless explicitly configured.