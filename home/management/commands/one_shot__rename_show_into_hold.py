from home.management.abstract_command import AbstractCommand
from home.models import Sentence
from scraping.extract_v2.models import EventMotion


class Command(AbstractCommand):
    help = "One shot command to rename SHOW into HOLD."

    def handle(self, *args, **options):
        counter = 0
        for sentence in Sentence.objects.all():
            if sentence.ml_confession_legacy \
                    and EventMotion(sentence.ml_confession_legacy) == EventMotion.SHOW:
                sentence.ml_confession_legacy = EventMotion.HOLD
            if sentence.human_confession_legacy \
                    and EventMotion(sentence.human_confession_legacy) == EventMotion.SHOW:
                sentence.human_confession_legacy = EventMotion.HOLD
            sentence.save()

            counter += 1
            if counter % 100 == 0:
                self.stdout.write(f'Processed {counter} sentences...')

        self.success(f'Successfully rename {counter} sentence v2 fields.')
