"""
URL configuration for the payouts' app.

Exposes the PayoutViewSet under the /api/payouts/ path via a DRF router.
"""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.payouts.views import PayoutViewSet

router = DefaultRouter()
router.register("payouts", PayoutViewSet, basename="payout")

urlpatterns = [
    path("", include(router.urls)),
]
