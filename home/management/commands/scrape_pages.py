from home.management.abstract_command import AbstractCommand
from home.models import Website
from scraping.scrape.download_refine_and_extract import get_fresh_extracted_html_list
from scraping.services.scrape_page_service import upsert_extracted_html_list


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
                extracted_html_list = get_fresh_extracted_html_list(page.url)

                if not extracted_html_list:
                    self.error(f'Failed to scrape page {page.url}')
                    continue

                # Insert or update scraping
                upsert_extracted_html_list(page, extracted_html_list)
                self.info(f'Successfully scraped page {page.url} {page.uuid}')

            self.success(f'Successfully scraped website {website.name} {website.uuid}')
