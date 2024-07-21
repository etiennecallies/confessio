from tqdm import tqdm

from home.management.abstract_command import AbstractCommand
from home.models import Scraping, ScrapingModeration
from scraping.services.prune_scraping_service import prune_scraping_and_save


class Command(AbstractCommand):
    help = "Fill indices of all scrapings and scrapings moderations"

    def handle(self, *args, **options):
        self.info(f'Starting repruning all scrapings')
        scrapings = Scraping.objects.filter(confession_html_pruned__isnull=False,
                                            indices__isnull=True).all()
        for scraping in tqdm(scrapings):
            if 'mailpoet' in scraping.confession_html:
                self.warning(f'Found mailpoet in scraping {scraping.uuid}. Deleting')
                scraping.delete()
                continue
            prune_scraping_and_save(scraping)

        self.info('Counting scraping moderations without confession_html')
        scraping_moderations_without_indices = ScrapingModeration.objects\
            .filter(confession_html__isnull=True).count()
        self.info(f'Found {scraping_moderations_without_indices} scraping moderations '
                  f'without confession_html')

        self.success(f'Successfully filled all indices')

