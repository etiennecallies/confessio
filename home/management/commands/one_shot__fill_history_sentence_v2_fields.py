from home.management.abstract_command import AbstractCommand
from home.models import Sentence


class Command(AbstractCommand):
    help = "One shot command to fill history sentence v2 fields."

    def handle(self, *args, **options):
        counter = 0
        for sentence in Sentence.objects.all():
            assert sentence.ml_specifier is not None
            Sentence.history.model.objects.filter(
                uuid=sentence.uuid,
                ml_specifier__isnull=True
            ).update(ml_specifier=sentence.ml_specifier)

            assert sentence.ml_schedule is not None
            Sentence.history.model.objects.filter(
                uuid=sentence.uuid,
                ml_schedule__isnull=True
            ).update(ml_schedule=sentence.ml_schedule)

            assert sentence.ml_confession_legacy is not None
            Sentence.history.model.objects.filter(
                uuid=sentence.uuid,
                ml_confession_legacy__isnull=True
            ).update(ml_confession_legacy=sentence.ml_confession_legacy)

            counter += 1
            if counter % 100 == 0:
                self.stdout.write(f'Processed {counter} sentences...')

        self.success(f'Successfully fill {counter} history sentence v2 fields.')
