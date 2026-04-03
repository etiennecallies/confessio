from core.management.abstract_command import AbstractCommand
from registry.services.church_location_service import find_church_geo_outliers


class Command(AbstractCommand):
    help = "Check that church locations are not absurd"

    def handle(self, *args, **options):
        self.info('Starting checking church locations are not absurd')
        outliers_count = find_church_geo_outliers()
        self.success(f'{outliers_count} outliers found')
