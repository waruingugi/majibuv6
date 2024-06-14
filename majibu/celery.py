from __future__ import absolute_import, unicode_literals

import os
from typing import Any

from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aviator.settings")

app = Celery(
    __name__, timezone="Africa/Nairobi", broker_connection_retry_on_startup=True
)

# Configure Celery using settings from Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load tasks from all registered Django configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


# Period tasks in the system
scheduled_tasks: dict[str, Any] = {}

app.conf.update({"beat_schedule": scheduled_tasks})
