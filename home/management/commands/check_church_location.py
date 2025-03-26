from statistics import mean

from home.management.abstract_command import AbstractCommand
from home.models import Diocese
from sourcing.utils.geo_utils import get_geo_distance


class Command(AbstractCommand):
    help = "Check church location are not absurd"

    def handle(self, *args, **options):
        self.info(f'Starting checking church location')

        avg_diocese_distances_by_church = {}
        avg_parish_distances_by_church = {}
        for diocese in Diocese.objects.all():
            self.info(f'Scanning diocese {diocese.name}')
            diocese_churches = []
            for parish in diocese.parishes.all():
                parish_churches = []
                for church in parish.churches.all():
                    diocese_churches.append(church)
                    parish_churches.append(church)

                if len(parish_churches) > 1:
                    for i in range(len(parish_churches)):
                        church1 = parish_churches[i]
                        church1_distances = []
                        for j in range(len(parish_churches)):
                            church2 = parish_churches[j]
                            church1_distances.append(
                                get_geo_distance(church1.location, church2.location))

                        church_slug = f'{diocese.messesinfo_network_id} {church1.name}'
                        avg_parish_distances_by_church[church_slug] = mean(church1_distances)

            for i in range(len(diocese_churches)):
                church1 = diocese_churches[i]
                church1_distances = []
                for j in range(len(diocese_churches)):
                    church2 = diocese_churches[j]
                    church1_distances.append(get_geo_distance(church1.location, church2.location))

                church_slug = f'{diocese.messesinfo_network_id} {church1.name}'
                avg_diocese_distances_by_church[church_slug] = mean(church1_distances)

        # Diocese sort dict by value
        self.info(f'Sorting diocese churches by average distance')
        avg_diocese_distances_by_church = sorted(avg_diocese_distances_by_church.items(),
                                                 key=lambda item: item[1], reverse=True)
        for church_slug, avg_distance in avg_diocese_distances_by_church[:5]:
            self.info(f'{church_slug} has an average distance of {round(avg_distance / 1000)} km '
                      f'with other diocese churches')

        # Parish sort dict by value
        self.info(f'Sorting parish churches by average distance')
        avg_parish_distances_by_church = sorted(avg_parish_distances_by_church.items(),
                                                key=lambda item: item[1], reverse=True)
        for church_slug, avg_distance in avg_parish_distances_by_church[:5]:
            self.info(f'{church_slug} has an average distance of {round(avg_distance / 1000)} km '
                      f'with other parish churches')

        self.success('Done')
