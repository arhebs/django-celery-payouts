"""
Service layer for payouts.

Encapsulates business logic for creating and updating payouts so that
views and tasks remain thin orchestration layers.
"""

from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.payouts.models import Payout, StatusChoices
from apps.payouts.tasks import process_payout_task


class PayoutService:
    """Business operations for Payout objects."""

    @staticmethod
    @transaction.atomic
    def create_payout(validated_data: dict[str, Any]) -> Payout:
        """Create a payout and dispatch the Celery processing task."""
        payout = Payout.objects.create(**validated_data)

        transaction.on_commit(
            lambda: process_payout_task.delay(str(payout.id)),
        )

        return payout

    @staticmethod
    def can_update(payout: Payout) -> bool:
        """Return True if the payout can be updated via the API."""
        return payout.status == StatusChoices.PENDING

    @staticmethod
    @transaction.atomic
    def update_status(payout: Payout, new_status: str) -> Payout:
        """Atomically update payout status (used from Celery task)."""
        payout.status = new_status
        payout.save(update_fields=["status", "updated_at"])
        return payout

