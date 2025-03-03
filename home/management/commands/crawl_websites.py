import time
from datetime import timedelta

from django.db.models import F, Q
from django.utils import timezone

from home.management.abstract_command import AbstractCommand
from home.models import Website, WebsiteModeration
from scraping.services.crawl_website_service import crawl_website


class Command(AbstractCommand):
    help = "Launch the search of all urls with confessions hours, starting for home url"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of website to crawl')
        parser.add_argument('-t', '--timeout', help='timeout in seconds', type=int, default=0)
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

        timeout_reached = False
        start_time = time.time()
        nb_websites_crawled = 0

        for website in websites:
            if options['timeout'] and time.time() - start_time > options['timeout']:
                timeout_reached = True
                break

            self.info(f'Starting crawling for website {website.name} {website.uuid}')

            got_pages_with_content, some_pages_visited, error_detail = crawl_website(website)
            nb_websites_crawled += 1

            if got_pages_with_content:
                self.success(f'Successfully crawled website {website.name} {website.uuid}')
            elif some_pages_visited:
                self.warning(f'No page found for website {website.name} {website.uuid}')
            else:
                self.error(f'Error while crawling website {website.name} {website.uuid}')
                self.error(error_detail)

        if timeout_reached:
            self.warning(f'Timeout reached, stopping the command after {nb_websites_crawled} '
                         f'websites crawled')
        else:
            self.success(f'Successfully crawled all {nb_websites_crawled} websites')
