import time

from django.db.models import F, Min

from core.management.abstract_command import AbstractCommand
from registry.models import Website
from crawling.services.website_worker_service import worker_scrape_page


class Command(AbstractCommand):
    help = "Launch the scraping of all pages"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of website to crawl')
        parser.add_argument('-t', '--timeout', help='timeout in seconds', type=int, default=0)

    def handle(self, *args, **options):
        if options['name']:
            websites = Website.objects.filter(is_active=True, name__contains=options['name']).all()
        else:
            websites = Website.objects.filter(is_active=True, pages__isnull=False) \
                .annotate(earliest_update=Min('pages__scraping__updated_at')) \
                .order_by(F('earliest_update').asc(nulls_first=True))

        timeout_ts = None
        if options['timeout']:
            timeout_ts = int(time.time()) + options['timeout']

        self.info(f'Enqueuing scraping pages...')
        counter = 0
        for website in websites:
            counter += 1
            worker_scrape_page(str(website.uuid), timeout_ts)
        self.success(f'Enqueued {counter} websites for scrape pages.')
