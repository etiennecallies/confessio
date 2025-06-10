import time

from django.db.models import Max

from home.management.abstract_command import AbstractCommand
from home.management.utils.heartbeat_utils import ping_heartbeat
from home.models import Church
from sourcing.services.sync_trouverunemesse_service import sync_trouverunemesse_for_church, \
    sync_trouverunemesse_location_and_name
from sourcing.utils.trouverunemesse_utils import fetch_by_last_update, fetch_trouverunemesse_by_slug


class Command(AbstractCommand):
    help = "Sync with trouverunemesse.fr API"

    def add_arguments(self, parser):
        parser.add_argument('-d', '--diocese', help='diocese messesinfo_network_id to sync')
        parser.add_argument('-a', '--all', help='sync all churches', action='store_true')
        parser.add_argument('-t', '--timeout', help='timeout in seconds', type=int, default=0)

    def handle(self, *args, **options):
        if not options['all'] and not options['diocese']:
            self.handle_from_last_updated_at(timeout=options['timeout'])
            return

        if options['diocese']:
            churches = Church.objects.filter(
                parish__diocese__messesinfo_network_id=options['diocese'])
        else:
            churches = Church.objects.all()

        self.handle_for_churches(churches, timeout=options['timeout'])

    def handle_for_churches(self, churches: list[Church], timeout: int = 0):
        self.info(f'Starting syncing with trouverunemesse.fr API for specific churches')
        nb_churches = 0
        nb_no_result = 0
        nb_location_differs = 0
        nb_location_moderation = 0
        nb_name_differs = 0
        nb_name_moderation = 0

        start_time = time.time()

        for church in churches:
            if timeout and time.time() - start_time > timeout:
                self.warning(f'Timeout reached, stopping the command')
                break

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

    def handle_from_last_updated_at(self, timeout: int = 0):
        max_updated_at = Church.objects\
            .aggregate(Max('trouverunemesse_updated_at'))['trouverunemesse_updated_at__max']
        self.info(f'Starting syncing with trouverunemesse.fr API from last updated at: '
                  f'{max_updated_at}')

        start_time = time.time()

        page = 1
        while True:
            if timeout and time.time() - start_time > timeout:
                self.warning(f'Timeout reached, stopping the command')
                break

            trouver_une_messes_churches = fetch_by_last_update(page=page,
                                                               min_last_update=max_updated_at)
            if not trouver_une_messes_churches:
                break

            self.info(f'Processing page {page} with {len(trouver_une_messes_churches)} churches...')
            for trouverunemesse_church in trouver_une_messes_churches:
                trouverunemesse_last_update = trouverunemesse_church.last_update
                try:
                    church = Church.objects.filter(
                        trouverunemesse_id=trouverunemesse_church.id).get()
                    if church.trouverunemesse_updated_at == \
                            trouverunemesse_last_update:
                        print(f"Church {church.name} already has the latest "
                              f'trouverunemesse_updated_at, skipping sync.')
                        continue

                    church.trouverunemesse_updated_at = trouverunemesse_last_update
                    church.save()
                    print(f"Updating church {church.name} location and name from "
                          f'trouverunemesse.')
                    sync_trouverunemesse_location_and_name(church, trouverunemesse_church)
                    continue
                except Church.DoesNotExist:
                    pass

                if trouverunemesse_church.messesinfo_id is None:
                    print(f"Church {trouverunemesse_church.name} has no messesinfo_id, "
                          f'reloading it from slug.')
                    trouverunemesse_church = fetch_trouverunemesse_by_slug(
                        trouverunemesse_church.slug)

                try:
                    church = Church.objects.filter(
                        messesinfo_id=trouverunemesse_church.messesinfo_id).get()
                    print(f"Found church {church.name} with messesinfo_id "
                          f'{trouverunemesse_church.messesinfo_id}, updating it.')
                    church.trouverunemesse_id = trouverunemesse_church.id
                    church.trouverunemesse_slug = trouverunemesse_church.slug
                    church.trouverunemesse_updated_at = trouverunemesse_last_update
                    church.save()
                    sync_trouverunemesse_location_and_name(church, trouverunemesse_church)
                    continue
                except Church.DoesNotExist:
                    pass

            page += 1

        ping_heartbeat("HEARTBEAT_TROUVERUNEMESSE_URL")
        self.success(f'Successfully imported churches from trouverunemesse.')
