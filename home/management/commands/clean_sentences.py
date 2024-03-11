from home.management.abstract_command import AbstractCommand
from home.models import Sentence
from scraping.services.prune_scraping_service import tags_from_sentence
from scraping.utils.tag_line import get_tags_with_regex


class Command(AbstractCommand):
    help = "Clean sentences that have same tags given by regex"

    def handle(self, *args, **options):
        sentences = Sentence.objects.all()

        total_deleted = 0
        total_not_deleted = 0
        for sentence in sentences:
            if tags_from_sentence(sentence) == get_tags_with_regex(sentence.line):
                sentence.delete()
                total_deleted += 1
            else:
                total_not_deleted += 1

        self.success(f'Successfully deleted {total_deleted} sentences and '
                     f'{total_not_deleted} were kept')
