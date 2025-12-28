from home.management.abstract_command import AbstractCommand
from scheduling.models import Scheduling
from scheduling.process import parse_scheduling


class Command(AbstractCommand):
    help = "Parse scheduling in status PRUNED"

    def handle(self, *args, **options):
        self.info(f'Starting parse Schedulings in status PRUNED')
        schedulings = Scheduling.objects.filter(status=Scheduling.Status.PRUNED).all()
        for scheduling in schedulings:
            self.info(f'Processing scheduling {scheduling.uuid} '
                      f'for website {scheduling.website.name}')
            parse_scheduling(scheduling)
        self.success(f'Finished parsing {schedulings.count()} Schedulings')
