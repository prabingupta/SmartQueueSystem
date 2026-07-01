from django.apps import AppConfig


class QueueManagementConfig(AppConfig):
    """
    Core token booking and live queue engine.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.queue_management"
    verbose_name = "QueueManagement"

    def ready(self):
        # Import signals here once implemented, e.g.:
        # from apps.queue_management import signals  # noqa
        pass
