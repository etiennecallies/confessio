from tqdm import tqdm

from home.management.abstract_command import AbstractCommand
from home.models import Pruning
from scraping.services.page_service import remove_pruning_if_orphan


class Command(AbstractCommand):
    help = "Delete pruning if orphan"

    def handle(self, *args, **options):
        counter = 0
        for pruning in tqdm(Pruning.objects.all()):
            if remove_pruning_if_orphan(pruning):
                counter += 1
        self.success(f'Successfully cleaned {counter} prunings')
