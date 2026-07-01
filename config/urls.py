"""
Root URL configuration for the Smart Queue Management System.

Each app owns its own urls.py; this file just includes them under sensible
prefixes and wires up admin, API docs, static/media serving in dev, and
custom error handlers.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Smart Queue Management System API",
        default_version="v1",
        description="AI-Powered Digital Queue & Crowd Monitoring Platform — REST API",
        contact=openapi.Contact(email="dev@smartqueue.gov.np"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Website (server-rendered pages: home, dashboards, booking, etc.)
    path("", include("apps.dashboard.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("queue/", include("apps.queue_management.urls")),
    path("offices/", include("apps.offices.urls")),
    path("operators/", include("apps.operators.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("crowd-ai/", include("apps.crowd_ai.urls")),
    path("reports/", include("apps.reports.urls")),

    # REST API (versioned)
    path("api/v1/", include("apps.api.urls")),

    # API documentation
    path("api/docs/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"),
    path("api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    try:
        import debug_toolbar

        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:
        pass

# Custom error handlers (views implemented in apps.core.views)
handler404 = "apps.core.views.error_404"
handler403 = "apps.core.views.error_403"
handler500 = "apps.core.views.error_500"
