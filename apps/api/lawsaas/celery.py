import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lawsaas.settings.dev")

app = Celery("lawsaas")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
