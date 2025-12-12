from fetching.process import nightly_synchronization
from home.management.abstract_command import AbstractCommand


class Command(AbstractCommand):
    help = "Nightly fetching and processing"

    def handle(self, *args, **options):
        self.info(f'Starting nightly fetching and processing')
        nightly_synchronization()
        self.success(f'Finished nightly fetching and processing')
