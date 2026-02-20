from django.urls import reverse

from core.management.abstract_command import AbstractCommand
from scheduling.models import Parsing
from scheduling.services.parsing.parsing_service import get_parsing_schedules_list
from scheduling.workflows.parsing.explain_schedule import get_explanation_from_schedule


class Command(AbstractCommand):
    help = "Test get_explanation_from_schedule on all schedules."

    def handle(self, *args, **options):
        counter = 0
        parsings = Parsing.objects.all()
        for parsing in parsings:
            schedules_list = get_parsing_schedules_list(parsing)
            if not schedules_list:
                continue

            for schedule in schedules_list.schedules:
                try:
                    explanation = get_explanation_from_schedule(schedule)
                    print(explanation)
                except Exception as e:
                    self.error(f'Error explaining schedule {schedule}: {e}')
                    print(parsing.uuid)
                    print(reverse('edit_parsing', parsing.uuid))
                    print(schedules_list)
                counter += 1

        self.success(f'Successfully explained {counter} schedules')
