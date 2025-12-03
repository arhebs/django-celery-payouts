"""
Admin configuration for the payouts' app.
"""

from __future__ import annotations

from django.contrib import admin

from apps.payouts.models import Payout


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    """Admin interface for the Payout model."""

    list_display = (
        "id",
        "amount",
        "currency",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "currency", "created_at")
    search_fields = ("id", "recipient_details")
