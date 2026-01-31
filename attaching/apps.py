from django.apps import AppConfig


class AttachingConfig(AppConfig):
    name = "attaching"

    def ready(self):
        import attaching.signals  # noqa
