"""Office directory API routes, mounted under /api/v1/offices/."""
from django.urls import path

from apps.offices import views

app_name = "offices_api"

urlpatterns = [
    path("", views.OfficeListView.as_view(), name="list"),
    path("<uuid:public_id>/", views.OfficeDetailView.as_view(), name="detail"),
]
