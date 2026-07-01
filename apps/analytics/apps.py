from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    """
    Statistics, dashboards and reporting data.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analytics"
    verbose_name = "Analytics"

    def ready(self):
        # Import signals here once implemented, e.g.:
        # from apps.analytics import signals  # noqa
        pass
