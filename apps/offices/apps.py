from django.apps import AppConfig


class OfficesConfig(AppConfig):
    """
    Government office and branch management.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.offices"
    verbose_name = "Offices"

    def ready(self):
        # Import signals here once implemented, e.g.:
        # from apps.offices import signals  # noqa
        pass
