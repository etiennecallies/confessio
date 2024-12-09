from home.management.abstract_command import AbstractCommand
from home.models import Parsing
from scraping.services.parse_pruning_service import get_parsing_schedules_list


class Command(AbstractCommand):
    help = "One shot command to fill llm_json."

    def handle(self, *args, **options):
        counter = 0
        for parsing in Parsing.objects.all():
            if parsing.llm_json is not None:
                # Skip parsing with llm_json
                continue

            schedules_list = get_parsing_schedules_list(parsing)
            if schedules_list is None:
                # Skip parsing without schedules
                continue

            llm_json = schedules_list.model_dump()
            parsing.llm_json = llm_json
            parsing.save()
            counter += 1

        self.success(f'Successfully fill {counter} llm_json.')
