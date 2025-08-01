from home.management.abstract_command import AbstractCommand
from home.models import Page


class Command(AbstractCommand):
    help = "One shot command to fill page_new of scraping."

    def handle(self, *args, **options):
        self.info('Starting one shot command to fill page_new...')
        counter = 0
        for page in Page.objects.all():
            if page.scraping:
                page.scraping.page_new = page
                page.scraping.save()
                counter += 1
            else:
                self.warning(f'Page {page.id} has no scraping, skipping.')

        self.success(f'Successfully filled {counter} page_new in scraping.')
