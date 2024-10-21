from home.management.abstract_command import AbstractCommand
from home.models import Parsing, ParsingModeration
from home.templatetags.custom_tags import get_url
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
                to_print = False
                try:
                    print(get_explanation_from_schedule(schedule))
                except Exception as e:
                    self.error(f'Error explaining schedule {schedule}: {e}')
                    to_print = True

                # TODO clean this
                if to_print or "PAS IMPLEMENTE" in get_explanation_from_schedule(schedule):
                    print(parsing.uuid)
                    for parsing_moderation in ParsingModeration.objects.filter(
                            parsing=parsing).all():
                        print(f"https://confessio.fr{get_url(parsing_moderation)}")
                    print(schedules_list)
                counter += 1

        self.success(f'Successfully explained {counter} schedules')
