from home.management.abstract_command import AbstractCommand
from home.models import Website
from scheduling.process import init_scheduling


class Command(AbstractCommand):
    help = "Init scheduling for a website."

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of website to crawl', required=True)

    def handle(self, *args, **options):
        self.info(f'Starting init scheduling for websites matching name: {options["name"]}')
        websites = Website.objects.filter(is_active=True, name__contains=options['name']).all()
        for website in websites:
            self.info(f'Processing website: {website.name} (ID: {website.uuid})')
            init_scheduling(website)
        self.success(f'Finished init scheduling for websites matching name: {options["name"]}')
