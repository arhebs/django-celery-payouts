"""
ViewSet implementations for the payouts application.
"""

from __future__ import annotations

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from apps.payouts.filters import PayoutFilter
from apps.payouts.models import Payout
from apps.payouts.serializers import PayoutSerializer, PayoutUpdateSerializer
from apps.payouts.services import PayoutService


@extend_schema(tags=["Payouts"])
@extend_schema_view(
    list=extend_schema(
        summary="List payouts",
        description="Retrieve a paginated list of payouts with optional filtering.",
    ),
    create=extend_schema(
        summary="Create payout",
        description="Create a new payout and enqueue it for asynchronous processing.",
        examples=[
            OpenApiExample(
                "Create payout example",
                value={
                    "amount": "250.00",
                    "currency": "EUR",
                    "recipient_details": {
                        "account_number": "DE89370400440532013000",
                        "bank_name": "Deutsche Bank",
                    },
                    "description": "Contractor payment - March 2025",
                },
            )
        ],
    ),
)
class PayoutViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payouts via the REST API.

    Creation is delegated to the service layer, and updates are restricted
    to payouts that are still in the PENDING status.
    """

    queryset = Payout.objects.all()
    serializer_class = PayoutSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PayoutFilter

    def get_serializer_class(self):
        """Return serializer based on action (create/read vs. update)."""
        if self.action in ["partial_update", "update"]:
            return PayoutUpdateSerializer
        return PayoutSerializer

    def perform_create(self, serializer: PayoutSerializer) -> None:
        """
        Delegate creation to the service layer and attach instance.
        """
        payout = PayoutService.create_payout(serializer.validated_data)
        serializer.instance = payout

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Allow updates only for PENDING payouts."""
        instance = self.get_object()
        if not PayoutService.can_update(instance):
            return Response(
                {"detail": "Only PENDING payouts can be updated."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        """Allow partial updates only for PENDING payouts."""
        instance = self.get_object()
        if not PayoutService.can_update(instance):
            return Response(
                {"detail": "Only PENDING payouts can be updated."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().partial_update(request, *args, **kwargs)
