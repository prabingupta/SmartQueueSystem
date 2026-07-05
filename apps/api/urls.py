"""
Versioned REST API root. Each domain app exposes its own routes here as
it's built out.
"""
from django.urls import include, path

app_name = "api"

urlpatterns = [
    path("accounts/", include("apps.accounts.api_urls")),
    # Populated per-app in later phases:
    # path("queue/", include("apps.queue_management.api_urls")),
]
