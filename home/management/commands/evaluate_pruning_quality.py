from home.management.abstract_command import AbstractCommand
from scheduling.models.pruning_models import Pruning


class Command(AbstractCommand):
    help = "Evaluate pruning quality"

    def handle(self, *args, **options):
        total_prunings = 0
        total_v1_correct = 0
        total_v2_correct = 0
        total_v1_and_v2_correct = 0
        total_no_correct = 0
        for pruning in Pruning.objects.filter(human_indices__isnull=False).all():
            total_prunings += 1
            v1_correct = pruning.human_indices == pruning.ml_indices
            v2_correct = pruning.human_indices == pruning.v2_indices
            if v1_correct and not v2_correct:
                total_v1_correct += 1
            elif not v1_correct and v2_correct:
                total_v2_correct += 1
            elif v1_correct and v2_correct:
                total_v1_and_v2_correct += 1
            else:
                total_no_correct += 1
        self.info(f'Got {total_prunings} prunings with human indices')
        self.info(f'Got {total_v1_correct} prunings with v1 indices correct '
                  f'({total_v1_correct / total_prunings * 100:.2f} %)')
        self.info(f'Got {total_v2_correct} prunings with v2 indices correct '
                  f'({total_v2_correct / total_prunings * 100:.2f} %)')
        self.info(f'Got {total_v1_and_v2_correct} prunings with both v1 and v2 indices correct '
                  f'({total_v1_and_v2_correct / total_prunings * 100:.2f} %)')
        self.info(f'Got {total_no_correct} prunings with no correct indices '
                  f'({total_no_correct / total_prunings * 100:.2f} %)')
