"""
Test settings for the payout management service.

Uses SQLite for the database and forces Celery to run tasks eagerly so
tests execute synchronously.
"""

from __future__ import annotations

from .base import *  # noqa: F401,F403

DEBUG = False

ENVIRONMENT = "test"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Celery configuration for tests: run tasks synchronously
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

