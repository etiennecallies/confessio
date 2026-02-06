from core.management.abstract_command import AbstractCommand
from scheduling.models import Scheduling
from scheduling.services.scheduling.scheduling_process_service import match_scheduling


class Command(AbstractCommand):
    help = "Parse scheduling in status PARSED"

    def handle(self, *args, **options):
        self.info(f'Starting match Schedulings in status PARSED')
        schedulings = Scheduling.objects.filter(status=Scheduling.Status.PARSED).all()
        for scheduling in schedulings:
            self.info(f'Processing scheduling {scheduling.uuid} '
                      f'for website {scheduling.website.name}')
            match_scheduling(scheduling)
        self.success(f'Finished matching {schedulings.count()} Schedulings')
