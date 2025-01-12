from home.management.abstract_command import AbstractCommand
from home.models import Parsing, ParsingModeration
from scraping.services.parse_pruning_service import add_parsing_moderation


class Command(AbstractCommand):
    help = "One shot command to fill add missing ParsingModeration."

    def handle(self, *args, **options):
        counter = 0
        for parsing in Parsing.objects.filter(moderations__isnull=True,
                                              prunings__scrapings__page__isnull=False).all():
            add_parsing_moderation(parsing, ParsingModeration.Category.NEW_SCHEDULES)
            counter += 1

        self.success(f'Successfully created {counter} llm_json.')
