from django.apps import AppConfig


class OperatorsConfig(AppConfig):
    """
    Counter operator actions and workflow.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.operators"
    verbose_name = "Operators"

    def ready(self):
        # Import signals here once implemented, e.g.:
        # from apps.operators import signals  # noqa
        pass
