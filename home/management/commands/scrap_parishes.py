from django.core.management.base import BaseCommand, CommandError

from home.models import Parish, Scrapping
from scrapping.search_confessions_paragraph import get_fresh_confessions_part


class Command(BaseCommand):
    help = "Launch the scrapping of all parishes"

    def handle(self, *args, **options):
        parishes = Parish.objects.all()

        for parish in parishes:
            # Actually do the scrapping
            url_to_scrap = parish.confession_hours_url
            confession_part = get_fresh_confessions_part(url_to_scrap, 'html_page')

            # Compare result to last scrapping
            last_scrapping = parish.scrappings.latest('updated_at')
            if last_scrapping is not None and last_scrapping.confession_html == confession_part:
                # If a scrapping exists and is identical to last one
                last_scrapping.nb_iterations += 1
                last_scrapping.save()
            else:
                new_scrapping = Scrapping(
                    confession_html=confession_part,
                    nb_iterations=1,
                    parish=parish,
                )
                new_scrapping.save()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully scrapped parish {parish.name} {parish.uuid}')
            )
