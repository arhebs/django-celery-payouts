"""
Tests for the payout service layer.
"""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import patch

import pytest

from apps.payouts.models import Payout, StatusChoices
from apps.payouts.services import PayoutService


@pytest.mark.django_db
class TestPayoutServiceCreatePayout:
    @patch("apps.payouts.services.transaction.on_commit")
    @patch("apps.payouts.services.process_payout_task.delay")
    def test_create_payout_dispatches_task(
            self,
            mock_delay,
            mock_on_commit,
            valid_payout_data: Dict[str, Any],
    ) -> None:
        mock_on_commit.side_effect = lambda func, *args, **kwargs: func()

        payout = PayoutService.create_payout(valid_payout_data)

        assert isinstance(payout, Payout)
        assert payout.status == StatusChoices.PENDING
        mock_delay.assert_called_once_with(str(payout.id))


@pytest.mark.django_db
class TestPayoutServiceUpdateStatus:
    def test_can_update_only_pending(self, payout: Payout, completed_payout: Payout) -> None:
        assert PayoutService.can_update(payout) is True
        assert PayoutService.can_update(completed_payout) is False

    def test_update_status_changes_status(self, payout: Payout) -> None:
        updated = PayoutService.update_status(payout, StatusChoices.COMPLETED)

        assert updated.status == StatusChoices.COMPLETED
        payout.refresh_from_db()
        assert payout.status == StatusChoices.COMPLETED
