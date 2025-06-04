from home.management.abstract_command import AbstractCommand
from home.models import Church


class Command(AbstractCommand):
    help = "One shot fill church search name and city"

    def handle(self, *args, **options):
        counter = 0
        for church in Church.objects.all():
            church.save()
            counter += 1

        self.success(f'Successfully fill {counter} churches.')
