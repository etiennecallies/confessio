from home.management.abstract_command import AbstractCommand
from home.models import ChurchTrouverUneMesse, Church
from sourcing.utils.trouverunemesse_utils import fetch_by_last_update


class Command(AbstractCommand):
    help = "One shot command to import all churches from trouverunemesse."

    def handle(self, *args, **options):
        self.info('Starting one shot command to import churches from trouverunemesse...')
        page = 1
        while True:
            trouver_une_messes_churches = fetch_by_last_update(page=page)
            if not trouver_une_messes_churches:
                break

            self.info(f'Processing page {page} with {len(trouver_une_messes_churches)} churches...')
            for trouverunemesse_church in trouver_une_messes_churches:
                if Church.objects.filter(trouverunemesse_id=trouverunemesse_church.id).exists():
                    continue

                church_trouverunemesse = ChurchTrouverUneMesse(
                    trouverunemesse_id=trouverunemesse_church.id,
                    trouverunemesse_slug=trouverunemesse_church.slug,
                    original_name=trouverunemesse_church.name,
                )
                church_trouverunemesse.save()

            page += 1
        self.success(f'Successfully imported churches from trouverunemesse.')
