from home.management.abstract_command import AbstractCommand
from scheduling.models.pruning_models import Sentence, Classifier
from scraping.services.classify_sentence_service import get_ml_label


class Command(AbstractCommand):
    help = "One shot command to fill ml_temporal fields."

    def handle(self, *args, **options):
        counter = 0
        for sentence in Sentence.objects.all():
            if sentence.ml_temporal is None:
                get_ml_label(sentence, Classifier.Target.TEMPORAL)

            counter += 1
            if counter % 100 == 0:
                self.stdout.write(f'Processed {counter} sentences...')

        self.success(f'Successfully fill {counter} ml_temporal fields.')
