"""
Root-level pages. The dashboard app owns "/" (public landing page) plus
the role-based dashboards, since those are the site's entry points.
"""
from django.urls import path

from apps.dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/citizen-preview/", views.citizen_dashboard_preview, name="citizen-dashboard-preview"),
]
