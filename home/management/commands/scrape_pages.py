from home.management.abstract_command import AbstractCommand
from home.models import Website
from scraping.services.scrape_page_service import upsert_scraping
from scraping.utils.download_and_extract import get_fresh_confessions_part


class Command(AbstractCommand):
    help = "Launch the scraping of all pages"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of website to crawl')

    def handle(self, *args, **options):
        if options['name']:
            websites = Website.objects.filter(is_active=True, name__contains=options['name']).all()
        else:
            websites = Website.objects.filter(is_active=True).all()

        for website in websites:
            self.info(f'Starting to scrape website {website.name} {website.uuid}')

            for page in website.get_pages():
                # Actually do the scraping
                confession_part = get_fresh_confessions_part(page.url)

                # Insert or update scraping
                upsert_scraping(page, confession_part)
                self.info(f'Successfully scrapped page {page.url} {page.uuid}')

            self.success(f'Successfully scrapped website {website.name} {website.uuid}')
