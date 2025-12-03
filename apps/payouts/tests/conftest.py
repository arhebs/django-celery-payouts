"""
Payout-specific pytest fixtures.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

import pytest
from django.utils import timezone

from apps.payouts.models import CurrencyChoices, Payout, StatusChoices


@pytest.fixture
def valid_payout_data() -> Dict[str, Any]:
    """Return a valid payload for creating a payout."""
    return {
        "amount": Decimal("100.00"),
        "currency": CurrencyChoices.USD,
        "recipient_details": {
            "account_number": "1234567890",
            "bank_name": "Example Bank",
        },
        "description": "Test payout",
    }


@pytest.fixture
def payout(db, valid_payout_data: Dict[str, Any]) -> Payout:
    """A payout in PENDING status."""
    return Payout.objects.create(**valid_payout_data)


@pytest.fixture
def completed_payout(db, valid_payout_data: Dict[str, Any]) -> Payout:
    """A payout in COMPLETED status."""
    payout_obj = Payout.objects.create(**valid_payout_data)
    payout_obj.status = StatusChoices.COMPLETED
    payout_obj.updated_at = timezone.now()
    payout_obj.save(update_fields=["status", "updated_at"])
    return payout_obj


@pytest.fixture
def processing_payout(db, valid_payout_data: Dict[str, Any]) -> Payout:
    """A payout in PROCESSING status."""
    payout_obj = Payout.objects.create(**valid_payout_data)
    payout_obj.status = StatusChoices.PROCESSING
    payout_obj.updated_at = timezone.now()
    payout_obj.save(update_fields=["status", "updated_at"])
    return payout_obj


@pytest.fixture
def failed_payout(db, valid_payout_data: Dict[str, Any]) -> Payout:
    """A payout in FAILED status."""
    payout_obj = Payout.objects.create(**valid_payout_data)
    payout_obj.status = StatusChoices.FAILED
    payout_obj.updated_at = timezone.now()
    payout_obj.save(update_fields=["status", "updated_at"])
    return payout_obj
