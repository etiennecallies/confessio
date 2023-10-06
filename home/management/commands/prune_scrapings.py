from django.core.management.base import BaseCommand

from home.models import Scraping
from scraping.utils.prune_content import prune_scraping


class Command(BaseCommand):
    help = "Prune content"

    def handle(self, *args, **options):
        scrapings = Scraping.objects.all()

        counter = 0
        for scraping in scrapings:
            prune_scraping(scraping)
            counter += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully pruned {counter} scrapings')
        )
