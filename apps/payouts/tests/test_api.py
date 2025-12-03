"""
API integration tests for the payouts endpoints.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.payouts.models import Payout, StatusChoices

pytestmark = pytest.mark.django_db


class TestPayoutCreateAPI:
    @patch("apps.payouts.services.transaction.on_commit")
    @patch("apps.payouts.services.process_payout_task.delay")
    def test_create_payout_success(
            self,
            mock_delay,
            mock_on_commit,
            client,
            valid_payout_data: Dict[str, Any],
    ) -> None:
        url = reverse("payout-list")
        payload = {
            "amount": "150.00",
            "currency": valid_payout_data["currency"],
            "recipient_details": valid_payout_data["recipient_details"],
            "description": "API create test",
        }

        # Ensure on_commit callbacks are executed immediately in this test,
        # so the Celery task mock is invoked.
        mock_on_commit.side_effect = lambda func, *args, **kwargs: func()

        response = client.post(url, data=payload, content_type="application/json")

        assert response.status_code == 201
        data = response.json()
        assert Decimal(data["amount"]) == Decimal("150.00")
        assert data["status"] == StatusChoices.PENDING
        assert "id" in data
        # Verify that the Celery task was dispatched with the created payout ID.
        mock_delay.assert_called_once_with(data["id"])

    def test_create_payout_validation_error(self, client, valid_payout_data: Dict[str, Any]) -> None:
        url = reverse("payout-list")
        payload = {
            "amount": "-10.00",
            "currency": valid_payout_data["currency"],
            "recipient_details": {},  # missing account_number
        }

        response = client.post(url, data=payload, content_type="application/json")

        assert response.status_code == 400
        data = response.json()
        assert "amount" in data
        assert "recipient_details" in data


class TestPayoutListAPI:
    def test_list_payouts(self, client, payout: Payout) -> None:
        url = reverse("payout-list")

        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) >= 1

    def test_filter_by_status(self, client, payout: Payout, completed_payout: Payout) -> None:
        url = reverse("payout-list")

        response = client.get(url, {"status": StatusChoices.PENDING})

        assert response.status_code == 200
        results = response.json()["results"]
        assert all(item["status"] == StatusChoices.PENDING for item in results)


class TestPayoutRetrieveAPI:
    def test_retrieve_payout(self, client, payout: Payout) -> None:
        url = reverse("payout-detail", args=[payout.id])

        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(payout.id)


class TestPayoutUpdateAPI:
    def test_update_pending_payout_success(self, client, payout: Payout) -> None:
        url = reverse("payout-detail", args=[payout.id])
        payload = {"amount": "200.00"}

        response = client.patch(url, data=payload, content_type="application/json")

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["amount"]) == Decimal("200.00")

    def test_update_non_pending_payout_forbidden(self, client, completed_payout: Payout) -> None:
        url = reverse("payout-detail", args=[completed_payout.id])
        payload = {"amount": "200.00"}

        response = client.patch(url, data=payload, content_type="application/json")

        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Only PENDING payouts can be updated."


class TestPayoutDeleteAPI:
    def test_delete_payout(self, client, payout: Payout) -> None:
        url = reverse("payout-detail", args=[payout.id])

        response = client.delete(url)

        assert response.status_code == 204
        assert not Payout.objects.filter(id=payout.id).exists()
