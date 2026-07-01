from django.apps import AppConfig


class ReportsConfig(AppConfig):
    """
    PDF/Excel/CSV report generation.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reports"
    verbose_name = "Reports"

    def ready(self):
        # Import signals here once implemented, e.g.:
        # from apps.reports import signals  # noqa
        pass
