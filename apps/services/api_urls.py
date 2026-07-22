"""Service directory API routes, mounted under /api/v1/services/."""
from django.urls import path

from apps.services import views

app_name = "services_api"

urlpatterns = [
    path("", views.ServiceListView.as_view(), name="list"),
    path("<uuid:public_id>/", views.ServiceDetailView.as_view(), name="detail"),
]
