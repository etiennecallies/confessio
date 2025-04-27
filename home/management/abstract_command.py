from datetime import datetime

from django.core.management import BaseCommand

from home.utils.log_utils import add_line_to_buffer


class AbstractCommand(BaseCommand):
    def handle(self, *args, **options):
        """
        The actual logic of the command. Subclasses must implement
        this method.
        """
        raise NotImplementedError(
            "subclasses of BaseCommand must provide a handle() method"
        )

    def log(self, m, modifier):
        message_to_log = f'{datetime.now()} {m}'
        self.stdout.write(modifier(message_to_log))
        add_line_to_buffer(message_to_log)

    def success(self, m):
        self.log(m, self.style.SUCCESS)

    def error(self, m):
        self.log(m, self.style.ERROR)

    def warning(self, m):
        self.log(m, self.style.WARNING)

    def info(self, m):
        self.log(m, self.style.HTTP_INFO)
