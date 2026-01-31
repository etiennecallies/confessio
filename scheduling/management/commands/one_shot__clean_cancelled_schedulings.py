from core.management.abstract_command import AbstractCommand
from scheduling.models import Scheduling


class Command(AbstractCommand):
    help = "One shot command to clean cancelled schedulings."

    def handle(self, *args, **options):
        self.info('Starting one shot command to clean cancelled schedulings.')

        counter = 0
        for scheduling in Scheduling.objects.filter(status='cancelled').all():
            scheduling.delete()
            counter += 1

        self.success(f'Successfully cleaned {counter} cancelled schedulings.')
