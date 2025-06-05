import asyncio
import time

from django.db.models import F
from django.db.models.functions import Now

from home.management.abstract_command import AbstractCommand
from home.models import Website, Log
from home.utils.log_utils import start_log_buffer, get_log_buffer
from scraping.scrape.download_refine_and_extract import get_fresh_extracted_html_list
from scraping.services.page_service import delete_page, clean_scraping_of_pruning
from scraping.services.prune_scraping_service import prune_pruning
from scraping.services.scrape_page_service import upsert_extracted_html_list


class Command(AbstractCommand):
    help = "Launch the scraping of all pages"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of website to crawl')
        parser.add_argument('-t', '--timeout', help='timeout in seconds', type=int, default=0)

    def handle(self, *args, **options):
        if options['name']:
            websites = Website.objects.filter(is_active=True, name__contains=options['name']).all()
        else:
            websites = Website.objects.filter(is_active=True, pages__isnull=False)\
                .order_by(F('pages__scraping__updated_at').asc(nulls_first=True)).all()

        start_time = time.time()

        for website in websites:
            if options['timeout'] and time.time() - start_time > options['timeout']:
                self.warning(f'Timeout reached, stopping the command')
                return

            start_log_buffer()
            self.info(f'Starting to scrape website {website.name} {website.uuid}')

            for page in website.get_pages():
                # Actually do the scraping
                with asyncio.Runner() as runner:
                    extracted_html_list = runner.run(get_fresh_extracted_html_list(page.url))

                if not extracted_html_list:
                    self.warning(f'No more content for {page.url}, deleting page {page.uuid}')
                    delete_page(page)

                    # Trigger a recrawl to make sure we don't miss anything
                    if website.crawling:
                        website.crawling.recrawl_triggered_at = Now()
                        website.crawling.save()
                    continue

                # Insert or update scraping
                prunings_to_prune = upsert_extracted_html_list(page, extracted_html_list)
                for pruning in prunings_to_prune:
                    clean_scraping_of_pruning(pruning)
                    prune_pruning(pruning)
                self.info(f'Successfully scraped page {page.url} {page.uuid}')

            self.success(f'Successfully scraped website {website.name} {website.uuid}')
            buffer_value = get_log_buffer()
            log = Log(type=Log.Type.SCRAPING,
                      website=website,
                      content=buffer_value)
            log.save()
