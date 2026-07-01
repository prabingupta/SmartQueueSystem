from django.apps import AppConfig


class CrowdAiConfig(AppConfig):
    """
    Computer vision crowd monitoring module.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.crowd_ai"
    verbose_name = "CrowdAi"

    def ready(self):
        # Import signals here once implemented, e.g.:
        # from apps.crowd_ai import signals  # noqa
        pass
