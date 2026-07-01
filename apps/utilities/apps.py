from django.apps import AppConfig


class UtilitiesConfig(AppConfig):
    """
    Cross-cutting helper functions.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.utilities"
    verbose_name = "Utilities"

    def ready(self):
        # Import signals here once implemented, e.g.:
        # from apps.utilities import signals  # noqa
        pass
