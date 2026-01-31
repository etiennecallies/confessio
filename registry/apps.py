from django.apps import AppConfig


class RegistryConfig(AppConfig):
    name = "registry"

    def ready(self):
        import registry.signals  # noqa
