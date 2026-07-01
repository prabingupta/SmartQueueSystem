from django.apps import AppConfig


class ServicesConfig(AppConfig):
    """
    Services offered per office.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.services"
    verbose_name = "Services"

    def ready(self):
        # Import signals here once implemented, e.g.:
        # from apps.services import signals  # noqa
        pass
