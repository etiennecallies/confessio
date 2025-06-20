from home.management.abstract_command import AbstractCommand
from home.models import Parsing
from scraping.parse.schedules import temp_convert_schedules_list_dict


class Command(AbstractCommand):
    help = "One shot command to convert parsing json."

    def handle(self, *args, **options):
        counter = 0
        for parsing in Parsing.objects.all():
            try:
                if parsing.llm_json is not None:
                    parsing.llm_json = temp_convert_schedules_list_dict(parsing.llm_json)\
                        .model_dump(mode='json')
                parsing.save()
                counter += 1
            except ValueError as e:
                print(parsing.llm_json)
                print(parsing.website_id)
                self.error(f'Error converting parsing {parsing.uuid} llm_json: {e}')

        for parsing in Parsing.objects.all():
            try:
                if parsing.human_json is not None:
                    parsing.human_json = temp_convert_schedules_list_dict(parsing.human_json)\
                        .model_dump(mode='json')
                parsing.save()
                counter += 1
            except ValueError as e:
                print(parsing.human_json)
                print(parsing.website_id)
                self.error(f'Error converting parsing {parsing.uuid} human_json: {e}')

        self.success(f'Successfully converted {counter} schedules.')
