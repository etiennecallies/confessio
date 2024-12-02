from home.management.abstract_command import AbstractCommand
from home.models import Scraping


class Command(AbstractCommand):
    help = "Delete all scrapings without page"

    def handle(self, *args, **options):
        Scraping.objects.filter(page=None).delete()
        self.success(f'Successfully deleted all scrapings without page')
