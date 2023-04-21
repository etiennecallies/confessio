from django.core.management.base import BaseCommand, CommandError

from home.models import Parish, Scraping
from scraping.search_confessions_paragraph import get_fresh_confessions_part


class Command(BaseCommand):
    help = "Launch the scraping of all parishes"

    def handle(self, *args, **options):
        parishes = Parish.objects.all()

        for parish in parishes:
            # Actually do the scraping
            url_to_scrap = parish.confession_hours_url
            confession_part = get_fresh_confessions_part(url_to_scrap, 'html_page')

            # Compare result to last scraping
            last_scraping = parish.get_latest_scraping()
            if last_scraping is not None and last_scraping.confession_html == confession_part:
                # If a scraping exists and is identical to last one
                last_scraping.nb_iterations += 1
                last_scraping.save()
            else:
                new_scraping = Scraping(
                    confession_html=confession_part,
                    nb_iterations=1,
                    parish=parish,
                )
                new_scraping.save()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully scrapped parish {parish.name} {parish.uuid}')
            )
