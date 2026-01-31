from home.management.abstract_command import AbstractCommand
from registry.models import Sentence
from scraping.extract_v2.models import EventMotion


class Command(AbstractCommand):
    help = "One shot command to fill human_confession."

    def handle(self, *args, **options):
        counter = 0
        for sentence in Sentence.objects.filter(human_confession_legacy__isnull=False).all():
            if sentence.human_confession is None:
                event_mention = EventMotion(sentence.human_confession_legacy).to_event_mention()
                sentence.human_confession = event_mention
                sentence.save()

                counter += 1

        self.success(f'Successfully fill {counter} human_confession.')
