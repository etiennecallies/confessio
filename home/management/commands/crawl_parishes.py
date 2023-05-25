from django.core.management.base import BaseCommand, CommandError

from home.models import Parish, Scraping, Page
from scraping.search_confessions_paragraphs import get_fresh_confessions_part
from scraping.search_confessions_urls import search_for_confession_pages


class Command(BaseCommand):
    help = "Launch the search of all urls with confessions hours, starting for home url"

    def handle(self, *args, **options):
        parishes = Parish.objects.all()

        for parish in parishes:
            if not parish.home_url:
                self.stdout.write(
                    self.style.WARNING(f'No home_url for this parish {parish.name} {parish.uuid}')
                )
                continue
            urls = search_for_confession_pages(parish.home_url)
            existing_urls = list(map(lambda p: p.url, parish.get_pages()))

            for url in urls:
                if url not in existing_urls:
                    new_page = Page(
                        url=url,
                        parish=parish
                    )
                    new_page.save()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully crawled parish {parish.name} {parish.uuid}')
            )
