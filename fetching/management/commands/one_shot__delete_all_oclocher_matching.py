from fetching.models import OClocherMatching
from home.management.abstract_command import AbstractCommand


class Command(AbstractCommand):
    help = "Delete all OClocherMatching entries"

    def handle(self, *args, **options):
        self.info(f'Starting delete all oclocher matchings')
        for oclocher_matching in OClocherMatching.objects.all():
            oclocher_matching.delete()

        for historical_matching in OClocherMatching.history.model.objects.all():
            historical_matching.delete()

        self.success(f'Finished delete all oclocher matchings')
