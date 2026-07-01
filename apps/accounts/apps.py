from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    User accounts, authentication and role management.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Accounts"

    def ready(self):
        # Import signals here once implemented, e.g.:
        # from apps.accounts import signals  # noqa
        pass
