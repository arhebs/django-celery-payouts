"""
Project configuration package.

Sets a sensible default ``DJANGO_SETTINGS_MODULE`` so Django can start
without requiring the environment variable to be defined explicitly, and
exposes the Celery application instance for worker processes.
"""

import os

from .celery import celery_app

DEFAULT_SETTINGS_MODULE = "config.settings.local"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", DEFAULT_SETTINGS_MODULE))

__all__ = ["celery_app"]
