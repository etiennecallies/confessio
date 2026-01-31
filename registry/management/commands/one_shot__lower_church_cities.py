from tqdm import tqdm

from core.management.abstract_command import AbstractCommand
from registry.models import Church
from registry.services.church_city_service import lower_church_city
from registry.utils.string_utils import has_two_consecutive_uppercase


class Command(AbstractCommand):
    help = "One shot command to lower church cities."

    def handle(self, *args, **options):
        self.info('Starting one shot command to lower church cities...')
        churches_to_norm = []
        for church in Church.objects.all():
            if church.zipcode and church.city and has_two_consecutive_uppercase(church.city):
                churches_to_norm.append(church)

        for church in tqdm(churches_to_norm):
            lower_church_city(church)

        self.success(f'Successfully lowered {len(churches_to_norm)} church cities.')
