import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("knowledge_assistant")

# Reads every CELERY_* setting from Django's settings.py (namespace= "CELERY" strips that prefix, so CELERY_BROKER_URL becomes broker_url internally).
app.config_from_object("django.conf:settings", namespace="CELERY")

# Scans INSTALLED_APPS for a tasks.py module in each app and imports it.
# This has to be autodiscover_tasks(), not a plain top-level `import tasks` here - this file is loaded very early (via config/__init__.py, before Django's settings/app registry are actually ready), and a direct import of a module that touches Django models (like ContentType) at that point would raise AppRegistryNotReady. autodiscover_tasks() defers the actual scanning until the app registry is ready, which is exactly why it's the documented pattern rather than something to reinvent.
app.autodiscover_tasks()