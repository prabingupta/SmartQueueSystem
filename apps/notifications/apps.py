from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """
    SMS and email notification dispatch.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    verbose_name = "Notifications"

    def ready(self):
        # Import signals here once implemented, e.g.:
        # from apps.notifications import signals  # noqa
        pass
