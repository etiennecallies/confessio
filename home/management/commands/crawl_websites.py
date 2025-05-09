import asyncio
import time
from datetime import timedelta

from django.db.models import F, Q
from django.utils import timezone

from home.management.abstract_command import AbstractCommand
from home.models import Website, WebsiteModeration, Log
from home.utils.log_utils import start_log_buffer, get_log_buffer
from scraping.services.crawl_website_service import crawl_website, split_websites_for_crawling


class Command(AbstractCommand):
    help = "Launch the search of all urls with confessions hours, starting for home url"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout_reached = False
        self.start_time = time.time()
        self.nb_websites_crawled = 0
        self.nb_websites_to_crawl = 0

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of website to crawl')
        parser.add_argument('-t', '--timeout', help='timeout in seconds', type=int, default=0)
        parser.add_argument('-p', '--parallel', help='nb of async threads', type=int, default=0)
        parser.add_argument('--in-error', action="store_true",
                            help='only websites with not validated home url moderation')
        parser.add_argument('--no-recent', action="store_true",
                            help='only websites that have not been crawled recently')

    def handle(self, *args, **options):
        if options['name']:
            websites = Website.objects.filter(is_active=True, name__contains=options['name']).all()
        elif options['in_error']:
            websites = Website.objects.filter(is_active=True).filter(
                Q(moderations__category__in=[
                    WebsiteModeration.Category.HOME_URL_NO_RESPONSE,
                    WebsiteModeration.Category.HOME_URL_NO_CONFESSION],
                    moderations__validated_at__isnull=True)
                | Q(crawling__recrawl_triggered_at__isnull=False)).all()
        elif options['no_recent']:
            websites = Website.objects.filter(is_active=True) \
                .filter(Q(crawling__isnull=True)
                        | Q(crawling__created_at__lt=timezone.now() - timedelta(hours=16))) \
                .order_by(F('crawling').asc(nulls_first=True)).all()
        else:
            websites = Website.objects.filter(is_active=True) \
                .order_by(F('crawling').asc(nulls_first=True)).all()

        websites = list(websites)
        self.nb_websites_to_crawl = len(websites)

        if options['parallel']:
            self.info(f'Starting crawling {self.nb_websites_to_crawl} websites in '
                      f'{options["parallel"]} threads')
            asyncio.run(self.handle_websites_in_parallel(websites, options['timeout'],
                                                         options['parallel']))
        else:
            self.info(f'Starting crawling {self.nb_websites_to_crawl} websites')
            asyncio.run(self.handle_websites(websites, options['timeout']))

        if self.timeout_reached:
            self.warning(f'Timeout reached, stopping the command after {self.nb_websites_crawled} '
                         f'websites crawled')
        else:
            self.success(f'Successfully crawled all {self.nb_websites_crawled} websites')

    async def handle_websites_in_parallel(self, websites_list: list[Website], timeout: int, n: int):
        tasks = []
        for websites in split_websites_for_crawling(websites_list, n):
            tasks.append(self.handle_websites(websites, timeout))

        await asyncio.gather(*tasks)

    async def handle_websites(self, websites: list[Website], timeout: int):
        nb_websites = len(websites)
        nb_websites_crawled_on_thread = 0

        for website in websites:
            if timeout and time.time() - self.start_time > timeout:
                self.timeout_reached = True
                break

            await self.handle_website(website)

            nb_websites_crawled_on_thread += 1
            self.nb_websites_crawled += 1
            self.info(f'{nb_websites_crawled_on_thread} / {nb_websites} websites crawled on thread '
                      f'({self.nb_websites_crawled} / {self.nb_websites_to_crawl} in total)')

    async def handle_website(self, website: Website):
        start_log_buffer()
        self.info(f'Starting crawling for website {website.name} {website.uuid}')

        got_pages_with_content, some_pages_visited = await crawl_website(website)

        if got_pages_with_content:
            self.success(f'Successfully crawled website {website.name} {website.uuid}')
        elif some_pages_visited:
            self.warning(f'No page found for website {website.name} {website.uuid}')
        else:
            self.error(f'Error while crawling website {website.name} {website.uuid}')
            if website.crawling:
                self.error(website.crawling.error_detail)
            else:
                self.error('No crawling found')

        buffer_value = get_log_buffer()
        log = Log(type=Log.Type.CRAWLING,
                  website=website,
                  content=buffer_value)
        await log.asave()
