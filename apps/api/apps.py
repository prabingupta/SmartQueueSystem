from django.apps import AppConfig


class ApiConfig(AppConfig):
    """
    REST API layer.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.api"
    verbose_name = "Api"

    def ready(self):
        # Import signals here once implemented, e.g.:
        # from apps.api import signals  # noqa
        pass
