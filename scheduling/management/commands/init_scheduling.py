from core.management.abstract_command import AbstractCommand
from registry.models import Website
from scheduling.services.scheduling.scheduling_process_service import init_scheduling


class Command(AbstractCommand):
    help = "Init scheduling for one or all website(s)."

    def add_arguments(self, parser):
        parser.add_argument('-n', '--name', help='name of website to crawl')
        parser.add_argument('--with-file-notes', action='store_true',
                            help='only websites having at least one file note')

    def handle(self, *args, **options):
        if options["name"]:
            self.info(f'Starting init scheduling for websites matching name: {options["name"]}')
            websites = Website.objects.filter(is_active=True, name__contains=options['name']).all()
        else:
            self.info('Starting init scheduling for all active websites')
            websites = Website.objects.filter(is_active=True).all()

        if options['with_file_notes']:
            websites = websites.filter(file_notes__isnull=False).distinct()

        for website in websites:
            self.info(f'Processing website: {website.name} (ID: {website.uuid})')
            init_scheduling(website)
        self.success(f'Finished init scheduling for {len(websites)} website(s)')
