"""
Project configuration package.

Sets a sensible default ``DJANGO_SETTINGS_MODULE`` so Django can start
without requiring the environment variable to be defined explicitly.
"""

import os

DEFAULT_SETTINGS_MODULE = "config.settings.local"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", DEFAULT_SETTINGS_MODULE))
