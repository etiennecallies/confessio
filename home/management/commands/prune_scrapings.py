from home.management.abstract_command import AbstractCommand
from home.models import Scraping
from scraping.services.prune_scraping_service import prune_scraping_and_save


class Command(AbstractCommand):
    help = "Prune content"

    def add_arguments(self, parser):
        parser.add_argument('--only-not-pruned', action="store_true",
                            help='prune only not pruned scraping')

    def handle(self, *args, **options):
        if options['only_not_pruned']:
            scrapings = Scraping.objects\
                .filter(page__parish__is_active=True, pruned_at__isnull=True).all()
        else:
            scrapings = Scraping.objects.filter(page__parish__is_active=True).all()

        counter = 0
        for scraping in scrapings:
            prune_scraping_and_save(scraping)
            counter += 1

        self.success(f'Successfully pruned {counter} scrapings')
