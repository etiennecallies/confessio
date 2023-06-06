from django.core.management.base import BaseCommand

from home.models import Parish, Page, Crawling
from scraping.search_confessions_urls import search_for_confession_pages


class Command(BaseCommand):
    help = "Launch the search of all urls with confessions hours, starting for home url"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of parish to crawl')

    def handle(self, *args, **options):
        if options['name']:
            parishes = Parish.objects.filter(name__contains=options['name']).all()
        else:
            parishes = Parish.objects.all()

        for parish in parishes:
            self.stdout.write(
                self.style.HTTP_INFO(f'Starting crawling for parish {parish.name} {parish.uuid}')
            )
            urls, nb_visited_links, error_detail = search_for_confession_pages(parish.home_url)
            success = error_detail is None
            crawling = Crawling(
                success=success,
                nb_visited_links=nb_visited_links,
                error_detail=error_detail,
                parish=parish,
            )
            crawling.save()

            if success:
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
            else:
                self.stdout.write(
                    self.style.ERROR(f'Error while crawling parish {parish.name} {parish.uuid}')
                )
                self.stdout.write(
                    self.style.ERROR(error_detail)
                )
