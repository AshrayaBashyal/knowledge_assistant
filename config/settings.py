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
    "memory"
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


# workspace-search
RESULTS_PER_SOURCE = int(os.getenv("RESULTS_PER_SOURCE","10"))


# Celery 
# Redis is used purely as the message broker (+ result backend for debugging) for now - task status that the app actually queries lives in our own models (ContentIndex, FlashcardSet), not Celery's result backend.
# Caching/rate-limiting uses of Redis later
CELERY_BROKER_URL = os.getenv("CELERY_REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_REDIS_URL", "redis://localhost:6379/0")

# Force both transport drivers to validate the SSL parameters explicitly
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'ssl': {
        'ssl_cert_reqs': ssl.CERT_REQUIRED
    }
}
CELERY_REDIS_BACKEND_TRANSPORT_OPTIONS = {
    'ssl': {
        'ssl_cert_reqs': ssl.CERT_REQUIRED
    }
}

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE