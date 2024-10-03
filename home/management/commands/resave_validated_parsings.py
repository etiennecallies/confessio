import json

from home.management.abstract_command import AbstractCommand
from home.models import ParsingModeration
from scraping.parse.schedules import SchedulesList, ScheduleItem


class Command(AbstractCommand):
    help = "Reformat validated schedules_list json of parsing_moderation."

    def handle(self, *args, **options):
        counter = 0
        parsing_moderations = ParsingModeration.objects.all()
        for parsing_moderation in parsing_moderations:
            if parsing_moderation.validated_schedules_list:
                # deep copy the dictionary to avoid modifying the original
                sl_dict = json.loads(json.dumps(parsing_moderation.validated_schedules_list))

                # create ScheduleItem objects from the dictionary and add missing exrule
                schedules = [ScheduleItem(**({'exrule': None} | s))
                             for s in sl_dict.pop('schedules')]

                schedules_list = SchedulesList(schedules=schedules, **sl_dict)
                parsing_moderation.validated_schedules_list = schedules_list.model_dump()
                parsing_moderation.save()

                counter += 1

        self.success(f'Successfully parsed {counter} pruning-websites')
