from home.management.abstract_command import AbstractCommand
from home.models import Parish, ParishModeration, Page
from scraping.services.crawl_parish_service import crawl_parish


class Command(AbstractCommand):
    help = "Launch the search of all urls with confessions hours, starting for home url"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of parish to crawl')
        parser.add_argument('--in-error', action="store_true",
                            help='only parishes with not validated home url moderation')

    def handle(self, *args, **options):
        self.info(f'Starting removing pages of inactive parishes')
        delete_count = 0
        for page in Page.objects.filter(website__is_active=False):
            page.delete()
            delete_count += 1
        self.success(f'Successfully deleted {delete_count} pages')

        if options['name']:
            parishes = Parish.objects.filter(is_active=True, name__contains=options['name']).all()
        elif options['in_error']:
            parishes = Parish.objects.filter(is_active=True).filter(
                moderations__category__in=[ParishModeration.Category.HOME_URL_NO_RESPONSE,
                                           ParishModeration.Category.HOME_URL_NO_CONFESSION],
                moderations__validated_at__isnull=True).all()
        else:
            parishes = Parish.objects.filter(is_active=True).all()

        for parish in parishes:
            self.info(f'Starting crawling for parish {parish.name} {parish.uuid}')

            got_pages_with_content, some_pages_visited, error_detail = crawl_parish(parish)

            if got_pages_with_content:
                self.success(f'Successfully crawled parish {parish.name} {parish.uuid}')
            elif some_pages_visited:
                self.warning(f'No page found for parish {parish.name} {parish.uuid}')
            else:
                self.error(f'Error while crawling parish {parish.name} {parish.uuid}')
                self.error(error_detail)
