from django.core.management.base import BaseCommand

from home.models import Scraping
from scraping.utils.refine_content import refine_confession_content


class Command(BaseCommand):
    help = "Refine all contents"

    def handle(self, *args, **options):
        scrapings = Scraping.objects.all()

        counter = 0
        for scraping in scrapings:

            scraping.confession_html_refined = refine_confession_content(scraping.confession_html)
            scraping.save()
            counter += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully refined {counter} scrapings')
        )
