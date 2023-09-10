from django.core.management.base import BaseCommand
from django.db.models.functions import Now

from home.models import Parish, Page, Crawling
from scraping.scrape_page import upsert_scraping
from scraping.search_confessions_urls import search_for_confession_pages


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

            # Actually crawling parish
            confession_part_by_url, nb_visited_links, error_detail = \
                search_for_confession_pages(parish.home_url)

            # Inserting global statistics
            crawling = Crawling(
                nb_visited_links=nb_visited_links,
                nb_success_links=len(confession_part_by_url),
                error_detail=error_detail,
                parish=parish,
            )
            crawling.save()

            # Removing old pages
            existing_pages = parish.get_pages()
            existing_urls = list(map(lambda p: p.url, existing_pages))
            for page in existing_pages:
                if page.url not in confession_part_by_url:
                    # Page did exist but not anymore
                    page.deleted_at = Now()
                    page.save()
                else:
                    # Page still exists, we update scraping
                    confession_part = confession_part_by_url[page.url]
                    upsert_scraping(page, confession_part)

            if confession_part_by_url:
                # Adding new pages
                for url in confession_part_by_url:
                    if url not in existing_urls:
                        # New page was found

                        new_page = Page(
                            url=url,
                            parish=parish
                        )
                        new_page.save()

                        # Insert or update scraping
                        confession_part = confession_part_by_url[url]
                        upsert_scraping(new_page, confession_part)

                self.stdout.write(
                    self.style.SUCCESS(f'Successfully crawled parish {parish.name} {parish.uuid}')
                )
            elif nb_visited_links > 0:
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
