"""
Versioned REST API root.

Each domain app will expose its own DRF routers under here in the
REST APIs phase, e.g.:

    path("accounts/", include("apps.accounts.api_urls")),
    path("queue/", include("apps.queue_management.api_urls")),
"""
from django.urls import path

app_name = "api"

urlpatterns = [
    # Populated per-app in the REST APIs phase.
]
