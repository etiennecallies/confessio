import json

from home.management.abstract_command import AbstractCommand
from home.models import ParsingModeration
from scraping.parse.schedules import SchedulesList


class Command(AbstractCommand):
    help = "Reformat validated schedules_list json of parsing_moderation."

    def handle(self, *args, **options):
        counter = 0
        parsing_moderations = ParsingModeration.objects.all()
        for parsing_moderation in parsing_moderations:
            if parsing_moderation.validated_schedules_list:
                # deep copy the dictionary to avoid modifying the original
                sl_dict = json.loads(json.dumps(parsing_moderation.validated_schedules_list))

                for schedule in sl_dict['schedules']:
                    if 'weekday' in schedule['rule']:
                        schedule['rule']['weekday_iso8601'] = schedule['rule']['weekday']
                        del schedule['rule']['weekday']

                schedules_list = SchedulesList(**sl_dict)
                parsing_moderation.validated_schedules_list = schedules_list.model_dump()
                parsing_moderation.save()

                counter += 1

        self.success(f'Successfully resaved {counter} pruning-websites')
