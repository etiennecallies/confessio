from django.db.models import Q

from home.management.abstract_command import AbstractCommand
from home.models import Sentence, Classifier
from scraping.services.classify_sentence_service import classify_existing_sentence
from scraping.services.train_classifier_service import set_label


class Command(AbstractCommand):
    help = "One shot command to fill ML sentence v2 fields."

    def handle(self, *args, **options):
        counter = 0
        for sentence in Sentence.objects.filter(Q(ml_specifier__isnull=True)
                                                | Q(ml_schedule__isnull=True)
                                                | Q(ml_confession__isnull=True)).all():
            if sentence.ml_specifier is None:
                ml_specifier, specifier_classifier = classify_existing_sentence(
                    sentence, Classifier.Target.SPECIFIER)
                set_label(sentence, ml_specifier, specifier_classifier)
            if sentence.ml_schedule is None:
                ml_schedule, schedule_classifier = classify_existing_sentence(
                    sentence, Classifier.Target.SCHEDULE)
                set_label(sentence, ml_schedule, schedule_classifier)
            if sentence.ml_confession is None:
                ml_confession, confession_classifier = classify_existing_sentence(
                    sentence, Classifier.Target.CONFESSION)
                set_label(sentence, ml_confession, confession_classifier)

            sentence.save()

            counter += 1
            if counter % 100 == 0:
                self.stdout.write(f'Processed {counter} sentences...')

        self.success(f'Successfully fill {counter} ML sentence v2 fields.')
