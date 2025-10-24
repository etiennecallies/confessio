from home.management.abstract_command import AbstractCommand
from home.models import Parish
from sourcing.services.sync_parishes_service import save_parish


class Command(AbstractCommand):
    help = "Add website to orphan parish"

    def handle(self, *args, **options):
        self.info(f'Starting finding websites to orphan parish')
        orphan_parishes = Parish.objects.exclude(
            diocese__messesinfo_network_id='lh'
        ).filter(
            website__isnull=True,
        ).all()

        counter = 0
        for parish in orphan_parishes:
            save_parish(parish)  # this will find a website if missing
            counter += 1

        self.success(f'Successfully found {counter} websites to orphan parish')
