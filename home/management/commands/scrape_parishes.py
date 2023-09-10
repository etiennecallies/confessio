from django.core.management.base import BaseCommand

from home.models import Parish
from scraping.scrape_page import upsert_scraping
from scraping.search_confessions_paragraphs import get_fresh_confessions_part


class Command(BaseCommand):
    help = "Launch the scraping of all parishes"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of parish to crawl')

    def handle(self, *args, **options):
        if options['name']:
            parishes = Parish.objects.filter(name__contains=options['name']).all()
        else:
            parishes = Parish.objects.all()

        for parish in parishes:
            self.stdout.write(
                self.style.HTTP_INFO(f'Starting to scrape parish {parish.name} {parish.uuid}')
            )

            for page in parish.get_pages():
                # Actually do the scraping
                confession_part = get_fresh_confessions_part(page.url, 'html_page')

                # Insert or update scraping
                upsert_scraping(page, confession_part)
                self.stdout.write(
                    self.style.HTTP_INFO(f'Successfully scrapped page {page.url} {page.uuid}')
                )

            self.stdout.write(
                self.style.SUCCESS(f'Successfully scrapped parish {parish.name} {parish.uuid}')
            )
