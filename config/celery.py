"""
Celery application for the Smart Queue Management System.

Used for:
- Sending SMS/email notifications asynchronously
- Processing camera frames for crowd detection off the request cycle
- Generating scheduled reports (daily/weekly/monthly)
- Computing hourly/daily crowd statistics
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("smart_queue_system")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
