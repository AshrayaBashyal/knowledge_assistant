import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-dev-key-change-in-production")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1")

# Hosts
allowed_hosts_raw = os.getenv("ALLOWED_HOSTS", "*")
ALLOWED_HOSTS = [
    host.strip()
    for host in allowed_hosts_raw.split(",")
    if host.strip()
]

# Optional packages
try:
    import whitenoise
    HAS_WHITENOISE = True
except ImportError:
    HAS_WHITENOISE = False

try:
    import cloudinary
    import cloudinary_storage
    HAS_CLOUDINARY = True
except ImportError:
    HAS_CLOUDINARY = False

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
USE_CLOUDINARY = HAS_CLOUDINARY and bool(CLOUDINARY_CLOUD_NAME)


# Application definition
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",

    # Local apps
    "apps.accounts",
    "apps.chat",
    "apps.documents",
    "apps.retrieval",
    "apps.notes",
    "apps.flashcards",
    "apps.memory",
    "apps.search",
    "apps.analytics",
]

# WhiteNoise runserver integration
if HAS_WHITENOISE:
    INSTALLED_APPS.insert(
        INSTALLED_APPS.index("django.contrib.staticfiles"),
        "whitenoise.runserver_nostatic",
    )

# Cloudinary must come AFTER django.contrib.staticfiles.
# This ensures Django's standard collectstatic command is used.
if USE_CLOUDINARY:
    INSTALLED_APPS.extend([
        "cloudinary_storage",
        "cloudinary",
    ])


# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
]

if HAS_WHITENOISE:
    MIDDLEWARE.append(
        "whitenoise.middleware.WhiteNoiseMiddleware"
    )

MIDDLEWARE.extend([
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.RequestLoggingMiddleware",
])


ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# Database
DATABASE_URL = os.getenv("DATABASE_URL")

DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600 if DATABASE_URL else 0,
        conn_health_checks=bool(DATABASE_URL),
    )
}


# Authentication
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE_BACKEND = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
    if HAS_WHITENOISE
    else "django.contrib.staticfiles.storage.StaticFilesStorage"
)


# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

if USE_CLOUDINARY:
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": CLOUDINARY_CLOUD_NAME,
        "API_KEY": os.getenv("CLOUDINARY_API_KEY"),
        "API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
    }

    DEFAULT_STORAGE_BACKEND = (
        "cloudinary_storage.storage.RawMediaCloudinaryStorage"
    )
else:
    DEFAULT_STORAGE_BACKEND = (
        "django.core.files.storage.FileSystemStorage"
    )

STORAGES = {
    "default": {
        "BACKEND": DEFAULT_STORAGE_BACKEND,
    },
    "staticfiles": {
        "BACKEND": STATICFILES_STORAGE_BACKEND,
    },
}

# Compatibility for django-cloudinary-storage 0.3.0,
# which accesses the legacy setting during collectstatic.
STATICFILES_STORAGE = STATICFILES_STORAGE_BACKEND

DOCUMENT_MAX_UPLOAD_SIZE_MB = int(
    os.getenv("DOCUMENT_MAX_UPLOAD_SIZE_MB", "60")
)


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "chat": os.getenv("RATELIMIT_CHAT_RATE", "30/m"),
        "login": os.getenv("RATELIMIT_LOGIN_RATE", "10/m"),
    },
}


# Redis cache
REDIS_CACHE_URL = os.getenv("REDIS_CACHE_URL", "")

if REDIS_CACHE_URL and REDIS_CACHE_URL.lower() != "none":
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_CACHE_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }


# API documentation
SPECTACULAR_SETTINGS = {
    "TITLE": "Knowledge Assistant API",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}


# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=120),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}


# CORS
cors_raw = os.getenv("CORS_ALLOWED_ORIGINS", "")

if cors_raw:
    CORS_ALLOWED_ORIGINS = [
        origin.strip()
        for origin in cors_raw.split(",")
        if origin.strip()
    ]
else:
    CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True


# CSRF
csrf_raw = os.getenv("CSRF_TRUSTED_ORIGINS", "")

if csrf_raw:
    CSRF_TRUSTED_ORIGINS = [
        origin.strip()
        for origin in csrf_raw.split(",")
        if origin.strip()
    ]
else:
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "https://*.onrender.com",
        "https://*.vercel.app",
    ]


# Chat
CHAT_HISTORY_MAX_MESSAGES = int(
    os.getenv("CHAT_HISTORY_MAX_MESSAGES", "20")
)


# Retrieval and vector database
CHROMA_PERSIST_DIR = (
    os.getenv("CHROMA_PERSIST_DIR")
    or str(BASE_DIR / "chroma_data")
)

RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "4"))

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))


# Tavily search
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
WEB_SEARCH_MAX_RESULTS = int(
    os.getenv("WEB_SEARCH_MAX_RESULTS", "3")
)


# Workspace search
RESULTS_PER_SOURCE = int(
    os.getenv("RESULTS_PER_SOURCE", "10")
)


# Celery
CELERY_TASK_ALWAYS_EAGER = (
    os.getenv("CELERY_TASK_ALWAYS_EAGER", "True").lower()
    in ("true", "1")
)

CELERY_TASK_EAGER_PROPAGATES = True

CELERY_REDIS_URL = os.getenv(
    "CELERY_REDIS_URL",
    "redis://localhost:6379/0",
)

CELERY_BROKER_URL = CELERY_REDIS_URL
CELERY_RESULT_BACKEND = CELERY_REDIS_URL

if CELERY_REDIS_URL.startswith("rediss://"):
    ssl_reqs = os.getenv("REDIS_SSL_CERT_REQS", "CERT_NONE")

    CELERY_BROKER_URL = (
        f"{CELERY_REDIS_URL}?ssl_cert_reqs={ssl_reqs}"
    )

    CELERY_RESULT_BACKEND = (
        f"{CELERY_REDIS_URL}?ssl_cert_reqs={ssl_reqs}"
    )

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE


# Logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "core.logging.JSONFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "app.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django.server": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
