from home.management.abstract_command import AbstractCommand
from scheduling.models import Scheduling
from scheduling.process import index_scheduling


class Command(AbstractCommand):
    help = "Index scheduling in status PARSED"

    def handle(self, *args, **options):
        self.info(f'Starting index Schedulings in status PARSED')
        schedulings = Scheduling.objects.filter(status=Scheduling.Status.PARSED).all()
        for scheduling in schedulings:
            self.info(f'Processing scheduling {scheduling.uuid} '
                      f'for website {scheduling.website.name}')
            index_scheduling(scheduling)
        self.success(f'Finished index {schedulings.count()} Schedulings')
