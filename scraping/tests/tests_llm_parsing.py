import json
import os
import unittest
from typing import Optional

import simple_cache
from dotenv import load_dotenv

from home.utils.date_utils import get_year_start, get_year_end
from scraping.parse.llm_client import LLMClientInterface, \
    LLMProvider
from scraping.parse.openai_provider import OpenAILLMClient, get_openai_client
from scraping.parse.parse_with_llm import parse_with_llm, get_prompt_template
from scraping.parse.rrule_utils import are_schedules_list_equivalent
from scraping.parse.schedules import SchedulesList, get_merged_schedules_list


class LLMClientWithCache(LLMClientInterface):
    llm_client: LLMClientInterface

    def __init__(self, llm_client: LLMClientInterface):
        self.llm_client = llm_client

    def get_completions(self,
                        messages: list[dict],
                        temperature: float) -> tuple[Optional[SchedulesList], Optional[str]]:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        cache_filename = (f'{current_directory}/fixtures/parse/'
                          f'llm_cache_{self.get_provider().value}.cache')

        key = (
            self.get_model(),
            json.dumps(messages),
            json.dumps(SchedulesList.model_json_schema()),
            temperature
        )
        value = simple_cache.load_key(cache_filename, key)

        if value is None:
            print('LLM Cache miss')
            value = self.llm_client.get_completions(messages, temperature)
            simple_cache.save_key(cache_filename, key, value,
                                  ttl=3600 * 24 * 365 * 100  # 100 years
                                  )

        return value

    def get_provider(self) -> LLMProvider:
        return self.llm_client.get_provider()

    def get_model(self) -> str:
        return self.llm_client.get_model()


class LlmParsingTests(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        openai_api_key = os.getenv("OPENAI_API_KEY") or 'thisIsNotARealKey'

        # llm_model = 'ft:gpt-4o-2024-08-06:confessio::AHfh95wJ'
        llm_model = 'gpt-4o-2024-08-06'

        self.llm_client = LLMClientWithCache(OpenAILLMClient(
            get_openai_client(openai_api_key),
            llm_model
        ))

    @staticmethod
    def get_simple_fixtures():
        return [
            'mock1',
            # 'st-georges',  # Not working, too long
            'paroisse2lyon',
            'azergues',
            'garches',
            'houilles',
            'stnomdejesus',
            'asnieres',
            'levallois',
            'levallois2',
            'ndlumieres',
            'carmel',
            # 'stnizier',  # Not working, too long
            'bron',
            'pierresdorees',
            'ste-therese',
            # 'chambourcy',  # an item is missing
            'vauxenvelin',
            'bonnieres',
            'gennevilliers',
            'fecamp',
            'nddelagare',
            'groscaillou',
            'bellecombe',
            'st-ambroise',
        ]

    def test_llm_parsing(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for file_name in self.get_simple_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/parse/{file_name}.html') as f:
                    lines = f.readlines()
                with open(f'{tests_dir}/fixtures/parse/{file_name}.json') as f:
                    input_and_output = json.load(f)
                truncated_html = ''.join(lines)
                church_desc_by_id = input_and_output['input']['church_desc_by_id']
                year = int(input_and_output['input']['year'])
                expected_schedules_list = SchedulesList(
                    **input_and_output['output']['schedules_list'])

                prompt_template = get_prompt_template()
                schedules_list, llm_error_detail = parse_with_llm(truncated_html, church_desc_by_id,
                                                                  prompt_template,
                                                                  llm_client=self.llm_client)
                self.assertIsNone(llm_error_detail, file_name)
                self.assertIsNotNone(schedules_list)
                # print(schedules_list.model_dump_json())

                year_start = get_year_start(year)
                year_end = get_year_end(year + 1)
                are_equivalent, reason = are_schedules_list_equivalent(
                    schedules_list, expected_schedules_list, year_start, year_end)

                self.assertTrue(are_equivalent, f'{reason} for {file_name}')

    @staticmethod
    def get_double_fixtures():
        return [
            'stsaturnin',
        ]

    def test_llm_parsing_with_cancellation(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for file_name in self.get_double_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/parse/{file_name}-1.html') as f:
                    lines1 = f.readlines()
                with open(f'{tests_dir}/fixtures/parse/{file_name}-2.html') as f:
                    lines2 = f.readlines()

                with open(f'{tests_dir}/fixtures/parse/{file_name}.json') as f:
                    input_and_output = json.load(f)

                church_desc_by_id = input_and_output['input']['church_desc_by_id']
                year = int(input_and_output['input']['year'])
                expected_schedules_list = SchedulesList(
                    **input_and_output['output']['schedules_list'])

                truncated_html1 = ''.join(lines1)
                prompt_template = get_prompt_template()
                schedules_list1, llm_error_detail1 = parse_with_llm(truncated_html1,
                                                                    church_desc_by_id,
                                                                    prompt_template,
                                                                    llm_client=self.llm_client)
                self.assertIsNone(llm_error_detail1)
                self.assertIsNotNone(schedules_list1)
                # print(schedules_list1.model_dump_json())

                truncated_html2 = ''.join(lines2)
                schedules_list2, llm_error_detail2 = parse_with_llm(truncated_html2,
                                                                    church_desc_by_id,
                                                                    prompt_template,
                                                                    llm_client=self.llm_client)
                self.assertIsNone(llm_error_detail2)
                self.assertIsNotNone(schedules_list2)
                # print(schedules_list2.model_dump_json())

                year_start = get_year_start(year)
                year_end = get_year_end(year + 1)

                merged_schedules_list = get_merged_schedules_list([
                    schedules_list1,
                    schedules_list2
                ])
                # print(merged_schedules_list.model_dump_json())
                are_equivalent, reason = are_schedules_list_equivalent(
                    merged_schedules_list, expected_schedules_list, year_start, year_end)

                self.assertTrue(are_equivalent, f'{reason} for {file_name}')


if __name__ == '__main__':
    unittest.main()
