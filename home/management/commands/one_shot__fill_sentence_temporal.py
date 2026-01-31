from home.management.abstract_command import AbstractCommand
from registry.models import Sentence
from scraping.extract_v2.models import Temporal


class Command(AbstractCommand):
    help = "One shot command to fill sentence human temporal."

    def handle(self, *args, **options):
        counter = 0
        for sentence in Sentence.objects.all():
            if sentence.human_specifier is not None or sentence.human_schedule is not None:
                assert sentence.human_specifier is not None and sentence.human_schedule is not None
                assert sentence.human_schedule is not True or sentence.human_specifier is not True

                human_temporal = Temporal.SPEC if sentence.human_specifier is True else (
                    Temporal.SCHED if sentence.human_schedule is True else Temporal.NONE
                )
                sentence.human_temporal = human_temporal
                sentence.save()

                counter += 1
                if counter % 100 == 0:
                    self.stdout.write(f'Processed {counter} sentences...')

        self.success(f'Successfully fill {counter} sentence human temporal.')
