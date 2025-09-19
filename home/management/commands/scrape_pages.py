from datetime import datetime, timedelta

from django.db.models import F

from home.management.abstract_command import AbstractCommand
from home.models import Website
from scraping.services.website_worker_service import worker_scrape_page


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
                .order_by(F('pages__scraping__updated_at').asc(nulls_first=True)).distinct()

        timeout_dt = None
        if options['timeout']:
            timeout_dt = datetime.now() + timedelta(seconds=options['timeout'])

        self.info(f'Enqueuing scraping pages...')
        counter = 0
        for website in websites:
            counter += 1
            worker_scrape_page(str(website.uuid), timeout_dt)
        self.success(f'Enqueued {counter} websites for scrape pages.')
