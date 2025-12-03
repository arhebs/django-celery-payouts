"""
Serializers for the payouts' application.

These serializers handle validation and representation of the Payout model
for both creation and update operations.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from rest_framework import serializers

from apps.payouts.models import Payout

_MAX_PAYOUT_AMOUNT = Decimal("999999999.99")


def _validate_amount_common(
        value: Decimal | None,
        allow_none: bool = False,
) -> Decimal | None:
    """Validate that amount is positive and within the configured maximum."""
    if value is None:
        if allow_none:
            return None
        raise serializers.ValidationError("Amount is required.")
    if value <= 0:
        raise serializers.ValidationError("Amount must be greater than zero.")
    if value > _MAX_PAYOUT_AMOUNT:
        raise serializers.ValidationError("Amount exceeds maximum allowed.")
    return value


def _validate_recipient_details_common(
        value: dict[str, Any] | None, allow_none: bool = False
) -> dict[str, Any] | None:
    """Validate the recipient_details payload and its account_number field."""
    if value is None:
        if allow_none:
            return None
        raise serializers.ValidationError("recipient_details is required.")
    if not isinstance(value, dict):
        raise serializers.ValidationError("Must be a JSON object.")
    if "account_number" not in value:
        raise serializers.ValidationError(
            "recipient_details must contain 'account_number'."
        )
    account = value.get("account_number", "")
    if not account or len(str(account)) < 5:
        raise serializers.ValidationError(
            "account_number must be at least 5 characters."
        )
    return value


class PayoutSerializer(serializers.ModelSerializer):
    """Serializer for creating and retrieving payouts."""

    class Meta:
        """Serializer metadata for full Payout representation."""

        model = Payout
        fields = [
            "id",
            "amount",
            "currency",
            "recipient_details",
            "status",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def validate_amount(self, value: Decimal) -> Decimal:
        """Validate amount for create operations."""
        validated = _validate_amount_common(value)
        assert validated is not None
        return validated

    def validate_recipient_details(self, value: dict[str, Any]) -> dict[str, Any]:
        """Validate recipient_details for create operations."""
        validated = _validate_recipient_details_common(value)
        assert validated is not None
        return validated


class PayoutUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating editable payout fields."""

    class Meta:
        """Serializer metadata for partial Payout updates."""

        model = Payout
        fields = ["amount", "currency", "recipient_details", "description"]

    def validate_amount(self, value: Decimal | None) -> Decimal | None:
        """Validate amount for update operations, allowing omission."""
        return _validate_amount_common(value, allow_none=True)

    def validate_recipient_details(
            self, value: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Validate recipient_details for update operations, allowing omission."""
        return _validate_recipient_details_common(value, allow_none=True)
