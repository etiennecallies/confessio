from django.core.management.base import BaseCommand

from home.models import Parish
from scraping.services.crawl_parish_service import crawl_parish


class Command(BaseCommand):
    help = "Launch the search of all urls with confessions hours, starting for home url"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of parish to crawl')
        parser.add_argument('--no-success', action="store_true",
                            help='exclude parishes that have been already successfully crawled')

    def handle(self, *args, **options):
        if options['name']:
            parishes = Parish.objects.filter(name__contains=options['name']).all()
        elif options['no_success']:
            parishes = Parish.objects.exclude(crawlings__nb_success_links__gt=0).all()
        else:
            parishes = Parish.objects.all()

        for parish in parishes:
            self.stdout.write(
                self.style.HTTP_INFO(f'Starting crawling for parish {parish.name} {parish.uuid}')
            )

            got_pages_with_content, some_pages_visited, error_detail = crawl_parish(parish)

            if got_pages_with_content:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully crawled parish {parish.name} {parish.uuid}')
                )
            elif some_pages_visited:
                self.stdout.write(
                    self.style.WARNING(f'No page found for parish {parish.name} {parish.uuid}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Error while crawling parish {parish.name} {parish.uuid}')
                )
                self.stdout.write(
                    self.style.ERROR(error_detail)
                )
