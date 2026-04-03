from django.core.management import call_command

from core.management.abstract_command import AbstractCommand
from core.utils.heartbeat_utils import ping_heartbeat


class Command(AbstractCommand):
    help = "Run all data integrity checks"

    def handle(self, *args, **options):
        self.info('Starting data checks')

        call_command('check_crawling_data')
        call_command('check_scheduling_data')
        call_command('check_registry_data')

        ping_heartbeat("HEARTBEAT_CHECK_DATA_URL")
        self.success('All data checks completed')
