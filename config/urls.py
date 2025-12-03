"""
Root URL configuration for the payout management service.

Currently exposes the Django admin; API routes will be added as the
implementation progresses.
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
