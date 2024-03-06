from home.management.abstract_command import AbstractCommand
from home.models import Parish
from scraping.services.scrape_page_service import upsert_scraping
from scraping.utils.download_and_extract import get_fresh_confessions_part


class Command(AbstractCommand):
    help = "Launch the scraping of all parishes"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of parish to crawl')

    def handle(self, *args, **options):
        if options['name']:
            parishes = Parish.objects.filter(is_active=True, name__contains=options['name']).all()
        else:
            parishes = Parish.objects.filter(is_active=True).all()

        for parish in parishes:
            self.info(f'Starting to scrape parish {parish.name} {parish.uuid}')

            for page in parish.get_pages():
                # Actually do the scraping
                confession_part = get_fresh_confessions_part(page.url, 'html_page')

                # Insert or update scraping
                upsert_scraping(page, confession_part)
                self.info(f'Successfully scrapped page {page.url} {page.uuid}')

            self.success(f'Successfully scrapped parish {parish.name} {parish.uuid}')
