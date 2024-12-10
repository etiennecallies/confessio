from home.management.abstract_command import AbstractCommand
from home.models import ParsingModeration
from scraping.parse.schedules import SchedulesList


class Command(AbstractCommand):
    help = "One shot command to fill human_json."

    def handle(self, *args, **options):
        counter = 0
        parsing_moderations = ParsingModeration.objects\
            .filter(validated_schedules_list__isnull=False).all()
        for parsing_moderation in parsing_moderations:
            parsing = parsing_moderation.parsing
            schedules_list = SchedulesList(**parsing_moderation.validated_schedules_list)
            parsing.human_json = schedules_list.model_dump()
            parsing.save()

            counter += 1

        self.success(f'Successfully filled {counter} human json')
