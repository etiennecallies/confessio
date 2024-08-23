from home.management.abstract_command import AbstractCommand
from home.models import Diocese, Page
from scraping.services.page_service import page_first_pruning_was_validated


class Command(AbstractCommand):
    help = "Evaluate pruning quality of pages of a given diocese"

    def add_arguments(self, parser):
        parser.add_argument('messesinfo_network_id', type=str,
                            help='Two letters code of messesinfo network_id (diocese)')

    def handle(self, *args, **options):
        messesinfo_network_id = options['messesinfo_network_id']
        try:
            diocese = Diocese.objects.get(messesinfo_network_id=messesinfo_network_id)
        except Diocese.DoesNotExist:
            self.error(f'No diocese for network_id {messesinfo_network_id}')
            return

        self.info(f'Getting page of diocese {diocese.name}...')
        pages = Page.objects.filter(website__parishes__diocese=diocese).distinct()
        self.info(f'Successfully got {len(pages)} pages')
        total_qualified = 0
        total_success = 0
        for page in pages:
            was_firstly_validated = page_first_pruning_was_validated(page)
            if was_firstly_validated is not None:
                total_qualified += 1

                if was_firstly_validated:
                    total_success += 1

        accuracy = total_success / total_qualified if total_qualified > 0 else 0
        self.success(f'Successfully got accuracy {accuracy * 100:.2f} %')
