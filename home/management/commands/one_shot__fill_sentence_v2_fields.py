from home.management.abstract_command import AbstractCommand
from registry.models import Sentence
from scraping.extract_v2.models import EventMotion, Temporal
from scraping.extract_v2.qualify_line_interfaces import RegexQualifyLineInterface
from scraping.prune.models import Action


class Command(AbstractCommand):
    help = "One shot command to fill sentence v2 fields."

    def handle(self, *args, **options):
        counter = 0
        qualify_line_interface = RegexQualifyLineInterface()
        for sentence in Sentence.objects.all():
            stringified_line = sentence.line
            temporal_tags, event_motion = \
                qualify_line_interface.get_temporal_and_event_mention_tags(stringified_line)

            if sentence.action in [Action.SHOW, Action.START]:
                if Temporal.SPEC in temporal_tags or sentence.action == Action.START:
                    spec = True
                else:
                    spec = False

                if Temporal.SCHED in temporal_tags:
                    sched = True
                else:
                    sched = False

                if event_motion == EventMotion.START:
                    confession_motion = EventMotion.START
                else:
                    confession_motion = EventMotion.SHOW
            else:
                spec = None
                if sentence.action == Action.HIDE:
                    sched = None
                    confession_motion = EventMotion.HIDE
                else:
                    sched = False
                    confession_motion = EventMotion.STOP

            sentence.ml_specifier = spec
            sentence.ml_schedule = sched
            sentence.ml_confession_legacy = confession_motion
            sentence.save()

            counter += 1
            if counter % 100 == 0:
                self.stdout.write(f'Processed {counter} sentences...')

        self.success(f'Successfully fill {counter} sentence v2 fields.')
