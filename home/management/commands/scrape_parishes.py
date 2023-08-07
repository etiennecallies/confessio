from django.core.management.base import BaseCommand, CommandError

from home.models import Parish, Scraping
from scraping.search_confessions_paragraphs import get_fresh_confessions_part
from scraping.utils.refine_content import refine_confession_content


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
                url_to_scrap = page.url
                confession_part = get_fresh_confessions_part(url_to_scrap, 'html_page')
                refined_html = refine_confession_content(confession_part)

                # Compare result to last scraping
                last_scraping = page.get_latest_scraping()
                if last_scraping is not None and last_scraping.confession_html == confession_part:
                    # If a scraping exists and is identical to last one
                    last_scraping.nb_iterations += 1
                    last_scraping.save()
                else:
                    new_scraping = Scraping(
                        confession_html=confession_part,
                        confession_html_refined=refined_html,
                        nb_iterations=1,
                        page=page,
                    )
                    new_scraping.save()
                self.stdout.write(
                    self.style.HTTP_INFO(f'Successfully scrapped page {page.url} {page.uuid}')
                )

            self.stdout.write(
                self.style.SUCCESS(f'Successfully scrapped parish {parish.name} {parish.uuid}')
            )
