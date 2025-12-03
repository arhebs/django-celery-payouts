"""
Celery application configuration for the payout management service.

This module exposes the ``celery_app`` instance used by workers and
ensures Celery is configured from Django settings with Redis as the
broker and result backend.
"""

from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

celery_app = Celery("django_celery_payouts")

# Load configuration from Django settings, using the CELERY_ prefix.
celery_app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks from installed Django apps.
celery_app.autodiscover_tasks()

