from statistics import mean

from home.management.abstract_command import AbstractCommand
from home.models import Diocese
from sourcing.utils.geo_utils import get_geo_distance


class Command(AbstractCommand):
    help = "Check church location are not absurd"

    def handle(self, *args, **options):
        self.info(f'Starting checking church location')

        avg_distances_by_church = {}
        for diocese in Diocese.objects.all():
            self.info(f'Scanning diocese {diocese.name}')
            diocese_churches = []
            for parish in diocese.parishes.all():
                for church in parish.churches.all():
                    diocese_churches.append(church)

            for i in range(len(diocese_churches)):
                church1 = diocese_churches[i]
                church1_distances = []
                for j in range(len(diocese_churches)):
                    church2 = diocese_churches[j]
                    church1_distances.append(get_geo_distance(church1.location, church2.location))

                church_slug = f'{diocese.messesinfo_network_id} {church1.name}'
                avg_distances_by_church[church_slug] = mean(church1_distances)

        # sort dict by value
        avg_distances_by_church = sorted(avg_distances_by_church.items(), key=lambda item: item[1],
                                         reverse=True)
        for church_slug, avg_distance in avg_distances_by_church[:5]:
            self.info(f'{church_slug} has an average distance of {round(avg_distance / 1000)} km '
                      f'with other diocese churches')

        self.success('Done')
