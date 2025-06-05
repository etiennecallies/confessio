from home.management.abstract_command import AbstractCommand
from sourcing.services.church_llm_name_service import compute_churches_llm_name


class Command(AbstractCommand):
    help = "One shot command to compute church llm name."

    def handle(self, *args, **options):
        self.info('Starting one shot command to compute church llm name...')
        compute_churches_llm_name(max_churches=15000)
        self.success(f'Successfully computed church llm names.')
