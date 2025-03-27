from home.management.abstract_command import AbstractCommand
from home.models import Diocese, Church
from sourcing.utils.geo_utils import get_distances_to_barycenter


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

                avg_parish_distances_by_church.update(
                    self.get_avg_distances_by_church(parish_churches, diocese)
                )

            avg_diocese_distances_by_church.update(
                self.get_avg_distances_by_church(diocese_churches, diocese)
            )

        # Diocese sort dict by value
        self.info(f'Sorting diocese churches by average distance')
        self.print_outliers(avg_diocese_distances_by_church)

        # Parish sort dict by value
        self.info(f'Sorting parish churches by average distance')
        self.print_outliers(avg_parish_distances_by_church)

        self.success('Done')

    @staticmethod
    def get_avg_distances_by_church(churches: list[Church], diocese: Diocese
                                    ) -> dict[str, float]:
        points = [c.location for c in churches]
        distance_by_point = get_distances_to_barycenter(points)

        avg_distances_by_church = {}
        for church in churches:
            church_slug = (f'{diocese.messesinfo_network_id} {church.name} '
                           f'{church.city}')
            avg_distances_by_church[church_slug] = distance_by_point[church.location]

        return avg_distances_by_church

    def print_outliers(self, avg_distances_by_church: dict[str, float]):
        avg_distances_by_church = sorted(avg_distances_by_church.items(),
                                         key=lambda item: item[1], reverse=True)
        for church_slug, avg_distance in avg_distances_by_church[:5]:
            self.info(f'{church_slug} has an average distance of {round(avg_distance / 1000)} km '
                      f'with other churches')
