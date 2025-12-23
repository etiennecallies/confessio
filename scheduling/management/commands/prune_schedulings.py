from home.management.abstract_command import AbstractCommand
from scheduling.models import Scheduling
from scheduling.process import prune_scheduling


class Command(AbstractCommand):
    help = "Prune scheduling in status BUILT"

    def handle(self, *args, **options):
        self.info(f'Starting prune Schedulings in status BUILT')
        schedulings = Scheduling.objects.filter(status=Scheduling.Status.BUILT).all()
        for scheduling in schedulings:
            self.info(f'Processing scheduling {scheduling.uuid} '
                      f'for website {scheduling.website.name}')
            prune_scheduling(scheduling)
        self.success(f'Finished pruning {schedulings.count()} Schedulings')
