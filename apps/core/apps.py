from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Shared base models, mixins and utilities.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

    def ready(self):
        # Import signals here once implemented, e.g.:
        # from apps.core import signals  # noqa
        pass
