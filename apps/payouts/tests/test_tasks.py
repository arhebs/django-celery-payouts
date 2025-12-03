"""
Tests for the process_payout_task Celery task.
"""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import patch

import pytest

from apps.payouts.models import Payout, StatusChoices
from apps.payouts.tasks import PayoutProcessingError, process_payout_task

pytestmark = pytest.mark.django_db


class TestProcessPayoutTask:
    @patch("apps.payouts.tasks.time.sleep")
    @patch("apps.payouts.tasks.random.random", return_value=0.5)
    def test_process_payout_success(
            self,
            mock_random: Any,
            mock_sleep: Any,
            payout: Payout,
    ) -> None:
        """Task should transition PENDING payout to COMPLETED on success."""
        assert payout.status == StatusChoices.PENDING

        result = process_payout_task.apply(args=(str(payout.id),)).get()

        payout.refresh_from_db()
        assert result.startswith("Completed:")
        assert payout.status == StatusChoices.COMPLETED
        mock_sleep.assert_called_once_with(5)

    def test_process_payout_skips_non_pending(self, completed_payout: Payout) -> None:
        """Task should skip payouts that are not in PENDING status."""
        assert completed_payout.status == StatusChoices.COMPLETED

        result = process_payout_task.apply(args=(str(completed_payout.id),)).get()

        completed_payout.refresh_from_db()
        assert result.startswith("Skipped:")
        assert completed_payout.status == StatusChoices.COMPLETED

    def test_on_failure_marks_failed(self, payout: Payout) -> None:
        """
        The task's on_failure handler should mark the payout as FAILED.

        This simulates Celery calling on_failure after all retries have been
        exhausted.
        """
        assert payout.status == StatusChoices.PENDING

        process_payout_task.on_failure(
            PayoutProcessingError("Simulated processing failure"),
            "test-task-id",
            (str(payout.id),),
            {},
            cast(Any, None),
        )

        payout.refresh_from_db()
        assert payout.status == StatusChoices.FAILED
