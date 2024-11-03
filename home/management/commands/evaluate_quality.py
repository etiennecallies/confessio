from typing import Literal

from home.management.abstract_command import AbstractCommand
from home.models import Diocese, Page
from scraping.services.page_service import page_was_validated_at_first


class Command(AbstractCommand):
    help = "Evaluate pruning and parsing quality of pages of a given diocese"

    def add_arguments(self, parser):
        parser.add_argument('messesinfo_network_id', type=str,
                            help='Two letters code of messesinfo network_id (diocese)')

    @staticmethod
    def evaluate_quality_for_resource(pages: list[Page],
                                      resource: Literal['pruning', 'parsing']) -> int:
        total_qualified = 0
        total_success = 0
        for page in pages:
            was_firstly_validated = page_was_validated_at_first(page, resource)
            if was_firstly_validated is not None:
                total_qualified += 1

                if was_firstly_validated:
                    total_success += 1

        return total_success / total_qualified if total_qualified > 0 else 0

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

        pruning_resource: Literal['pruning', 'parsing'] = 'pruning'
        parsing_resource: Literal['pruning', 'parsing'] = 'parsing'
        for resource in [pruning_resource, parsing_resource]:
            accuracy = self.evaluate_quality_for_resource(pages, resource)
            self.success(f'Got accuracy {accuracy * 100:.2f} % for {resource}')
