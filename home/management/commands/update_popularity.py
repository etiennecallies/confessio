from home.management.abstract_command import AbstractCommand
from home.services.popularity_service import update_popularity_of_websites


class Command(AbstractCommand):
    help = "Re-compute website popularity"

    def handle(self, *args, **options):
        self.info(f'Starting computing popularity of websites')
        update_popularity_of_websites()

        self.success(f'Finished computing popularity of websites')
