from fetching.process import nightly_synchronization
from core.management.abstract_command import AbstractCommand
from core.utils.heartbeat_utils import ping_heartbeat


class Command(AbstractCommand):
    help = "Nightly fetching and processing"

    def handle(self, *args, **options):
        self.info(f'Starting nightly fetching and processing')
        nightly_synchronization()
        ping_heartbeat("HEARTBEAT_NIGHTLY_FETCHING_URL")
        self.success(f'Finished nightly fetching and processing')
