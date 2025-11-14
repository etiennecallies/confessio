from home.management.abstract_command import AbstractCommand
from home.models import Sentence
from scraping.extract_v2.models import TemporalTag, EventMotion
from scraping.extract_v2.qualify_line_interfaces import RegexQualifyLineInterface
from scraping.prune.models import Action


class Command(AbstractCommand):
    help = "One shot command to fill sentence v2 fields."

    def handle(self, *args, **options):
        counter = 0
        qualify_line_interface = RegexQualifyLineInterface()
        for sentence in Sentence.objects.all():
            stringified_line = sentence.line
            tags, event_motion = qualify_line_interface.get_tags_and_event_motion(stringified_line)

            if sentence.action in [Action.SHOW, Action.START]:
                if TemporalTag.SPECIFIER in tags or sentence.action == Action.START:
                    spec = True
                else:
                    spec = False

                if TemporalTag.SCHEDULE in tags:
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
            sentence.ml_confession = confession_motion
            sentence.save()

            counter += 1
            if counter % 100 == 0:
                self.stdout.write(f'Processed {counter} sentences...')

        self.success(f'Successfully fill {counter} sentence v2 fields.')
