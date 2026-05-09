import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lawsaas.settings.dev")

app = Celery("lawsaas")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Beat schedule. Times are interpreted in CELERY_TIMEZONE
# (= America/Argentina/Buenos_Aires per base settings).
app.conf.beat_schedule = {
    "send-action-reminders-daily": {
        "task": "tenants.tasks.send_action_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
}
