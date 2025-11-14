from home.management.abstract_command import AbstractCommand
from home.models import Classifier


class Command(AbstractCommand):
    help = "Rename confession into confession_legacy."

    def handle(self, *args, **options):
        counter = 0
        for classifier in Classifier.objects.filter(target__exact=Classifier.Target.CONFESSION):
            classifier.target = Classifier.Target.CONFESSION_LEGACY
            classifier.save()

            counter += 1

        self.success(f'Successfully rename {counter} classifiers.')
