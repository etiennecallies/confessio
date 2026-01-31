from core.management.abstract_command import AbstractCommand
from front.templatetags.custom_tags import get_url
from scheduling.models.parsing_models import ParsingModeration, Parsing
from scraping.parse.explain_schedule import get_explanation_from_schedule
from scraping.services.parsing_service import get_parsing_schedules_list


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
                    for parsing_moderation in ParsingModeration.objects.filter(
                            parsing=parsing).all():
                        print(f"https://confessio.fr{get_url(parsing_moderation)}")
                    print(schedules_list)
                counter += 1

        self.success(f'Successfully explained {counter} schedules')
