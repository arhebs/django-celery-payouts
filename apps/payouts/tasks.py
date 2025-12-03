"""
Celery tasks for processing payouts.

Implements the asynchronous processing flow with retries and status
transitions according to the payout lifecycle.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any

from celery import Task, shared_task
from django.db import transaction

from apps.payouts.models import Payout, StatusChoices

logger = logging.getLogger(__name__)


class PayoutProcessingError(Exception):
    """Raised when payout processing fails."""


class PayoutTask(Task):
    """Base Celery task for payout processing with failure handling."""

    def on_failure(
            self,
            exc: Exception,
            task_id: str,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
            einfo: Any,
    ) -> None:
        """
        Handle task failure after retries are exhausted.

        Marks the associated payout as FAILED and then delegates to Celery's
        default on_failure implementation for standard logging/behavior.
        """
        payout_id = args[0] if args else None
        if payout_id:
            logger.error("Payout %s failed permanently: %s", payout_id, exc)
            with transaction.atomic():
                Payout.objects.filter(id=payout_id).update(
                    status=StatusChoices.FAILED,
                )
        super().on_failure(exc, task_id, args, kwargs, einfo)


@shared_task(
    bind=True,
    base=PayoutTask,
    autoretry_for=(PayoutProcessingError,),
    retry_backoff=True,
    retry_backoff_max=60,
    max_retries=3,
)
def process_payout_task(self: PayoutTask, payout_id: str) -> str:
    """
    Process a payout asynchronously.

    1. Set status to PROCESSING
    2. Simulate processing (5s delay)
    3. 10% chance of failure (demonstrates retry)
    4. Set status to COMPLETED or FAILED
    """
    logger.info("Processing payout %s, attempt %s", payout_id, self.request.retries + 1)

    with transaction.atomic():
        payout = Payout.objects.select_for_update().get(id=payout_id)

        if payout.status != StatusChoices.PENDING:
            logger.warning("Payout %s not PENDING, skipping", payout_id)
            return f"Skipped: status was {payout.status}"

        payout.status = StatusChoices.PROCESSING
        payout.save(update_fields=["status", "updated_at"])

    # Simulate external processing
    time.sleep(5)

    # 10% failure rate for demonstration
    if random.random() < 0.1:
        logger.warning("Payout %s processing failed, will retry", payout_id)
        # Reset to PENDING so retry can pick it up
        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(id=payout_id)
            payout.status = StatusChoices.PENDING
            payout.save(update_fields=["status", "updated_at"])
        raise PayoutProcessingError("Simulated processing failure")

    # Success
    with transaction.atomic():
        payout = Payout.objects.select_for_update().get(id=payout_id)
        payout.status = StatusChoices.COMPLETED
        payout.save(update_fields=["status", "updated_at"])

    logger.info("Payout %s completed successfully", payout_id)
    return f"Completed: {payout_id}"
