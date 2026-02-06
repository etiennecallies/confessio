from core.management.abstract_command import AbstractCommand
from front.services.search.popularity_service import update_popularity_of_websites


class Command(AbstractCommand):
    help = "Update popularity of websites based on recent hits"

    def handle(self, *args, **options):
        self.info(f'Starting computing popularity of websites')
        update_popularity_of_websites()
        self.success(f'Finished computing popularity of websites')
