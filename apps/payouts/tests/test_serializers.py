"""
Tests for payout serializers.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

import pytest

from apps.payouts.models import CurrencyChoices, Payout, StatusChoices
from apps.payouts.serializers import PayoutSerializer, PayoutUpdateSerializer


@pytest.mark.django_db
class TestPayoutSerializer:
    def test_valid_data_creates_payout(self, valid_payout_data: Dict[str, Any]) -> None:
        serializer = PayoutSerializer(data=valid_payout_data)

        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()

        assert isinstance(instance, Payout)
        assert instance.amount == Decimal("100.00")
        assert instance.currency == CurrencyChoices.USD
        assert instance.status == StatusChoices.PENDING

    @pytest.mark.parametrize(
        "amount",
        [Decimal("-1.00"), Decimal("0.00")],
    )
    def test_amount_must_be_positive(
            self,
            amount: Decimal,
            valid_payout_data: Dict[str, Any],
    ) -> None:
        data = {**valid_payout_data, "amount": amount}
        serializer = PayoutSerializer(data=data)

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_amount_cannot_exceed_maximum(self, valid_payout_data: Dict[str, Any]) -> None:
        data = {**valid_payout_data, "amount": Decimal("1000000000.00")}
        serializer = PayoutSerializer(data=data)

        assert not serializer.is_valid()
        assert "amount" in serializer.errors

    def test_recipient_details_requires_account_number(self, valid_payout_data: Dict[str, Any]) -> None:
        data = {**valid_payout_data, "recipient_details": {}}
        serializer = PayoutSerializer(data=data)

        assert not serializer.is_valid()
        assert "recipient_details" in serializer.errors


@pytest.mark.django_db
class TestPayoutUpdateSerializer:
    def test_partial_update_amount(self, payout: Payout) -> None:
        serializer = PayoutUpdateSerializer(
            instance=payout,
            data={"amount": "250.00"},
            partial=True,
        )

        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()

        assert instance.amount == Decimal("250.00")

    def test_update_serializer_allows_missing_fields(self, payout: Payout) -> None:
        serializer = PayoutUpdateSerializer(instance=payout, data={}, partial=True)

        assert serializer.is_valid(), serializer.errors
