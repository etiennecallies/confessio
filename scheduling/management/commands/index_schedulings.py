from core.management.abstract_command import AbstractCommand
from scheduling.models import Scheduling
from scheduling.process import index_scheduling


class Command(AbstractCommand):
    help = "Index scheduling in status MATCHED"

    def handle(self, *args, **options):
        self.info(f'Starting index Schedulings in status MATCHED')
        schedulings = Scheduling.objects.filter(status=Scheduling.Status.MATCHED).all()
        for scheduling in schedulings:
            self.info(f'Processing scheduling {scheduling.uuid} '
                      f'for website {scheduling.website.name}')
            index_scheduling(scheduling)
        self.success(f'Finished index {schedulings.count()} Schedulings')
