from tqdm import tqdm

from home.management.abstract_command import AbstractCommand
from home.models import Website
from scraping.services.index_events_service import index_events_for_website


class Command(AbstractCommand):
    help = "Re-index all events"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of website to crawl')

    def handle(self, *args, **options):
        if options['name']:
            websites = Website.objects.filter(is_active=True, name__contains=options['name']).all()
        else:
            websites = Website.objects.filter(is_active=True).all()

        websites = list(websites)
        self.info(f'Starting indexing {len(websites)} websites')
        for website in tqdm(websites):
            index_events_for_website(website)

        self.success(f'Successfully indexed all {len(websites)} websites')
