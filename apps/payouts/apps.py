"""
AppConfig for the payouts' application.
"""

from __future__ import annotations

from django.apps import AppConfig


class PayoutsConfig(AppConfig):
    """Django application configuration for the payouts' app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.payouts"
    verbose_name = "Payouts"
