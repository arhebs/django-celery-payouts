"""
Test settings for the payout management service.

By default, tests use an in-memory SQLite database for speed, but if a
``DATABASE_URL`` environment variable is provided (for example in CI),
the database configuration from ``base.py`` is preserved so tests run
against the configured database engine.
"""

from __future__ import annotations

import os

from .base import *  # noqa: F401,F403

DEBUG = False

ENVIRONMENT = "test"

# If DATABASE_URL is explicitly set (for example in CI), keep the database
# configuration derived from base settings. Otherwise, default to fast
# in-memory SQLite for local test runs.
if not os.getenv("DATABASE_URL"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

# Celery configuration for tests: run tasks synchronously
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
