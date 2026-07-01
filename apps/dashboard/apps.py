from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """
    Role-based dashboard views.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.dashboard"
    verbose_name = "Dashboard"

    def ready(self):
        # Import signals here once implemented, e.g.:
        # from apps.dashboard import signals  # noqa
        pass
