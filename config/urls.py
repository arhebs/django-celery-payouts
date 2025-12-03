"""
Root URL configuration for the payout management service.

Exposes the Django admin and the payouts API endpoints.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.payouts.urls")),
]
