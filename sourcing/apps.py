from django.apps import AppConfig


class SourcingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sourcing"

    def ready(self):
        import sourcing.signals  # noqa
