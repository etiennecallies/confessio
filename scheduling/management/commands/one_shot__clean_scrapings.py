from crawling.models import Scraping
from core.management.abstract_command import AbstractCommand
from scraping.services.scraping_service import delete_scraping


class Command(AbstractCommand):
    help = "One shot command to clean scrapings."

    def handle(self, *args, **options):
        self.info('Starting one shot command to clean scrapings...')

        counter = 0
        for scraping in Scraping.objects.filter(website__isnull=True).all():
            delete_scraping(scraping)
            counter += 1
            if counter % 10 == 0:
                self.info(f'Cleaned {counter} scrapings so far...')

        self.success(f'Successfully cleaned {counter} scrapings.')
