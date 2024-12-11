from home.management.abstract_command import AbstractCommand
from home.models import PruningModeration


class Command(AbstractCommand):
    help = "One shot command to fill human_indices."

    def handle(self, *args, **options):
        counter = 0
        for pruning_moderation in PruningModeration.objects.filter(validated_at__isnull=False)\
                .all():
            pruning = pruning_moderation.pruning

            pruning.human_indices = pruning_moderation.pruned_indices
            pruning.pruned_indices = pruning_moderation.pruned_indices
            pruning.save()
            counter += 1

        self.success(f'Successfully fill {counter} human_indices.')
