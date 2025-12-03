"""
Local development settings.

Extends ``base.py`` with development-friendly defaults such as ``DEBUG=True``.
"""

from __future__ import annotations

from .base import *  # noqa: F401,F403

DEBUG = True

ENVIRONMENT = "local"
