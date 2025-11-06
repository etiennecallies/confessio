from datetime import timedelta

from django.core.mail import mail_admins
from django.utils import timezone

from home.management.abstract_command import AbstractCommand
from home.management.utils.heartbeat_utils import ping_heartbeat
from home.models import Website, Crawling, ChurchIndexEvent
from home.utils.date_utils import get_current_day
from scraping.parse.holidays import check_holiday_by_zone
from scraping.parse.liturgical import check_easter_dates
from scraping.services.parse_pruning_service import check_website_parsing_relations, \
    debug_website_parsing_relations
from sourcing.services.church_location_service import find_church_geo_outliers


class Command(AbstractCommand):
    help = ("Check that latest nightly crawling has worked properly and sends an email to admins "
            "if not")

    def handle(self, *args, **options):
        self.info(f'Starting checking crawling')

        active_websites = Website.objects.filter(is_active=True).all()
        website_not_crawled = []
        website_not_crawled_recently = []
        website_not_parsed = []
        website_badly_linked_to_parsing = []
        for website in active_websites:
            try:
                crawling = website.crawling
            except Crawling.DoesNotExist:
                crawling = None

            if crawling is None:
                website_not_crawled.append(website)
                continue

            # check that latest crawling is no older than 24 hours
            if crawling.created_at < timezone.now() - timedelta(days=1) \
                    and website.enabled_for_crawling:
                website_not_crawled_recently.append(website)
                continue

            if not website.all_pages_parsed():
                website_not_parsed.append(website)

            if not check_website_parsing_relations(website):
                website_badly_linked_to_parsing.append(website)
                self.error(f'Website {website.name} {website.uuid} has bad parsing links')
                debug_website_parsing_relations(website)

        if website_not_crawled or website_not_crawled_recently or website_not_parsed \
                or website_badly_linked_to_parsing:
            error_message = (f'Crawling failure: {len(website_not_crawled)} websites have never '
                             f'been crawled and {len(website_not_crawled_recently)} have '
                             f'not been crawled recently and {len(website_not_parsed)} have not '
                             f'been parsed and {len(website_badly_linked_to_parsing)} with issues')
            self.error(error_message)
            website_not_crawled_str = "\n".join(
                [f" - {website.name} {website.uuid}" for website in website_not_crawled[:5]])
            website_not_crawled_recently_str = "\n".join(
                [f" - {website.crawling.created_at} {website.name} {website.uuid}"
                 for website in website_not_crawled_recently[:5]])
            website_not_parsed_str = "\n".join(
                [f" - {website.name} {website.uuid}" for website in website_not_parsed[:5]])
            website_badly_linked_to_parsing_str = "\n".join(
                [f" - {website.name} {website.uuid}"
                 for website in website_badly_linked_to_parsing[:5]])

            message = f"""
            Crawling failure

            Some websites not crawled (total {len(website_not_crawled)}):
            {website_not_crawled_str}

            Some websites not crawled recently (total {len(website_not_crawled_recently)}):
            {website_not_crawled_recently_str}

            Some websites not parsed (total {len(website_not_parsed)}):
            {website_not_parsed_str}

            Some websites with bad parsing links (total {len(website_badly_linked_to_parsing)}):
            {website_badly_linked_to_parsing_str}
            """
            mail_admins(subject=error_message, message=message)
            self.success(f'Email sent to admins')
        else:
            self.success(f'All websites have been crawled recently')

        self.info(f'Starting checking future holidays and easter dates')
        holiday_ok = check_holiday_by_zone()
        easter_ok = check_easter_dates()
        if not holiday_ok or not easter_ok:
            error_message = (f'Holiday failure: future holidays or easter dates are not '
                             f'implemented')
            self.error(error_message)
            message = f"""
            Holiday failure

            Future holidays or easter dates are not implemented
            Holiday: {holiday_ok}
            Easter: {easter_ok}
            """
            mail_admins(subject=error_message, message=message)
            self.success(f'Email sent to admins')
        else:
            self.success(f'All future holidays and easter dates are implemented')

        self.info('Starting checking church location are not absurd')
        outliers_count = find_church_geo_outliers()
        self.success(f'{outliers_count} outliers found')

        self.info(f'Starting checking index events')
        yesterday = get_current_day() - timedelta(days=1)
        if ChurchIndexEvent.objects.filter(day__lt=yesterday).exists():
            error_message = f'Index events exist from yesterday or before'
            self.error(error_message)
            message = f"""
            Index events exist from yesterday or before

            You shall check the index_events job.
            """
            mail_admins(subject=error_message, message=message)
            self.success(f'Email sent to admins')
        else:
            self.success(f'All index events are up to date')

        ping_heartbeat("HEARTBEAT_CHECK_CRAWLING_URL")
