from home.management.abstract_command import AbstractCommand
from home.models import Scraping


class Command(AbstractCommand):
    help = "One shot command to add pruning to scraping."

    def handle(self, *args, **options):
        counter = 0
        for scraping in Scraping.objects.all():
            if scraping.pruning is None:
                continue

            if scraping.pruning in scraping.prunings.all():
                continue

            scraping.prunings.add(scraping.pruning)
            counter += 1

        self.success(f'Successfully add {counter} prunings to scrapings.')
