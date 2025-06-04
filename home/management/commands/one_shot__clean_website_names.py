from home.management.abstract_command import AbstractCommand
from home.models import Website
from sourcing.services.website_name_service import clean_website_name


class Command(AbstractCommand):
    help = "One shot command to clean website names."

    def handle(self, *args, **options):
        self.info('Starting one shot command to clean website names...')

        counter = 0
        for website in Website.objects.all():
            if clean_website_name(website):
                counter += 1

        self.success(f'Successfully cleaned {counter} website names.')
