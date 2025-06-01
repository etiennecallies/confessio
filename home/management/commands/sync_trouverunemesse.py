from home.management.abstract_command import AbstractCommand
from home.models import Church
from sourcing.services.sync_trouverunemesse_service import sync_trouverunemesse_for_church


class Command(AbstractCommand):
    help = "Sync with trouverunemesse.fr API"

    def handle(self, *args, **options):
        self.info(f'Starting syncing with trouverunemesse.fr API')

        nb_churches = 0
        nb_no_result = 0
        nb_location_differs = 0
        nb_location_moderation = 0
        nb_name_differs = 0
        nb_name_moderation = 0

        for church in Church.objects.all():
            self.info(f'Processing church: {church.name} ({church.uuid})')
            nb_churches += 1
            result = sync_trouverunemesse_for_church(church)

            if result is None:
                nb_no_result += 1
            else:
                location_moderation_added, name_moderation_added = result
                if location_moderation_added is not None:
                    nb_location_differs += 1
                    if location_moderation_added:
                        nb_location_moderation += 1
                if name_moderation_added is not None:
                    nb_name_differs += 1
                    if name_moderation_added:
                        nb_name_moderation += 1

        self.success(f'Sync completed: {nb_churches} churches processed, '
                     f'{nb_no_result} with no result, '
                     f'{nb_location_differs} with location differs, '
                     f'{nb_location_moderation} location moderations added, '
                     f'{nb_name_differs} with name differs, '
                     f'{nb_name_moderation} name moderations added.')
