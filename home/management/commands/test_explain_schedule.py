from home.management.abstract_command import AbstractCommand
from home.models import Parsing
from scraping.parse.explain_schedule import get_explanation_from_schedule
from scraping.services.parse_pruning_service import get_parsing_schedules_list


class Command(AbstractCommand):
    help = "Test get_parsing_schedules_list on all schedules."

    def handle(self, *args, **options):
        counter = 0
        parsings = Parsing.objects.all()
        for parsing in parsings:
            schedules_list = get_parsing_schedules_list(parsing)
            for schedule in schedules_list.schedules:
                print(get_explanation_from_schedule(schedule))
                counter += 1

        self.success(f'Successfully explained {counter} schedules')
