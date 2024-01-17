from datetime import datetime

from django.core.management import BaseCommand


class AbstractCommand(BaseCommand):
    def handle(self, *args, **options):
        """
        The actual logic of the command. Subclasses must implement
        this method.
        """
        raise NotImplementedError(
            "subclasses of BaseCommand must provide a handle() method"
        )

    def log(self, m):
        self.stdout.write(f'{datetime.now()} {m}')

    def success(self, m):
        self.log(self.style.SUCCESS(m))

    def error(self, m):
        self.log(self.style.ERROR(m))

    def warning(self, m):
        self.log(self.style.WARNING(m))

    def info(self, m):
        self.log(self.style.HTTP_INFO(m))
