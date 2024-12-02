from home.management.abstract_command import AbstractCommand
from home.models import Pruning
from scraping.services.prune_scraping_service import prune_pruning


class Command(AbstractCommand):
    help = "Re-prune extracted html"

    def add_arguments(self, parser):
        parser.add_argument('--pruning-uuid', action='append',
                            default=[], help='uuid of pruning to prune (can be repeated)')

    def handle(self, *args, **options):
        if options['pruning_uuid']:
            prunings = Pruning.objects.filter(scrapings__temp_page__website__is_active=True,
                                              uuid__in=options['pruning_uuid']).distinct()
        else:
            prunings = Pruning.objects.filter(
                scrapings__temp_page__website__is_active=True
            ).distinct()

        counter = 0
        for pruning in prunings:
            prune_pruning(pruning)
            counter += 1

        self.success(f'Successfully pruned {counter} prunings')
