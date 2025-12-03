"""
Database models for the payouts application.
"""

from __future__ import annotations

import uuid

from django.db import models


class CurrencyChoices(models.TextChoices):
    """Supported payout currencies."""

    USD = "USD", "US Dollar"
    EUR = "EUR", "Euro"
    GBP = "GBP", "British Pound"
    RUB = "RUB", "Russian Ruble"


class StatusChoices(models.TextChoices):
    """Lifecycle states for a payout."""

    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


class Payout(models.Model):
    """
    Payout representing a single outgoing payment request.

    Uses a UUID primary key, stores the payout amount and currency, tracks
    lifecycle status, and keeps flexible recipient details in a JSON field.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.USD,
    )
    recipient_details = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payouts_payout"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Payout {self.id} - {self.amount} {self.currency} ({self.status})"
