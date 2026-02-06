import time
from datetime import timedelta

from django.db.models import F, Q
from django.utils import timezone

from core.management.abstract_command import AbstractCommand
from core.utils.log_utils import start_log_buffer
from crawling.models import CrawlingModeration
from crawling.services.website_worker_service import worker_crawl_website, handle_crawl_website
from registry.models import Website


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
        parser.add_argument('-u', '--uuid', help='uuid of website to crawl')
        parser.add_argument('-t', '--timeout', help='timeout in seconds', type=int, default=0)
        parser.add_argument('-d', '--direct', action="store_true",
                            help='crawl directly without going through the queue')
        parser.add_argument('--in-error', action="store_true",
                            help='only websites with not validated home url moderation')
        parser.add_argument('--no-recent', action="store_true",
                            help='only websites that have not been crawled recently')

    def handle(self, *args, **options):
        if options['name']:
            websites = Website.objects.filter(is_active=True, name__contains=options['name']).all()
        elif options['uuid']:
            websites = Website.objects.filter(is_active=True, uuid=options['uuid']).all()
        elif options['in_error']:
            websites = Website.objects.filter(is_active=True).filter(
                Q(crawling_moderation__category__in=[
                    CrawlingModeration.Category.NO_RESPONSE,
                    CrawlingModeration.Category.NO_PAGE],
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

        timeout_ts = None
        if options['timeout']:
            timeout_ts = int(time.time()) + options['timeout']

        self.info(f'Enqueuing crawling websites...')
        counter = 0
        for website in websites:
            counter += 1
            if options['direct']:
                start_log_buffer()
                handle_crawl_website(website)
            else:
                worker_crawl_website(str(website.uuid), timeout_ts)

        if options['direct']:
            self.success(f'Crawled {counter} websites directly.')
        else:
            self.success(f'Enqueued {counter} websites for crawling.')
