"""
Filter configuration for the payouts list endpoint.

Provides filtering by status, currency, creation date range, and amount
range using django-filter.
"""

from __future__ import annotations

import django_filters

from apps.payouts.models import Payout, StatusChoices


class PayoutFilter(django_filters.FilterSet):
    """FilterSet for querying payouts."""

    status = django_filters.ChoiceFilter(choices=StatusChoices.choices)
    currency = django_filters.CharFilter(lookup_expr="iexact")
    created_after = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
    )
    min_amount = django_filters.NumberFilter(
        field_name="amount",
        lookup_expr="gte",
    )
    max_amount = django_filters.NumberFilter(
        field_name="amount",
        lookup_expr="lte",
    )

    class Meta:
        """Metadata for payout filtering."""

        model = Payout
        fields = ["status", "currency"]

