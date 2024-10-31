import json
import os
import unittest
from typing import Optional

import simple_cache
from dotenv import load_dotenv

from home.utils.date_utils import get_year_start, get_year_end
from scraping.parse.llm_client import OpenAILLMClient, get_openai_client
from scraping.parse.parse_with_llm import parse_with_llm, get_prompt_template
from scraping.parse.rrule_utils import are_schedules_list_equivalent
from scraping.parse.schedules import SchedulesList, get_merged_schedules_list


class OpenAILLMClientWithCache(OpenAILLMClient):
    def get_completions(self,
                        model: str,
                        messages: list[dict],
                        temperature: float) -> tuple[Optional[SchedulesList], Optional[str]]:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        cache_filename = f'{current_directory}/fixtures/parse/llm_cache.cache'

        key = (model, json.dumps(messages), json.dumps(SchedulesList.model_json_schema()),
               temperature)
        value = simple_cache.load_key(cache_filename, key)

        if value is None:
            print('LLM Cache miss')
            value = super().get_completions(model, messages, temperature)
            simple_cache.save_key(cache_filename, key, value,
                                  ttl=3600 * 24 * 365 * 100  # 100 years
                                  )

        return value


class LlmParsingTests(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        openai_api_key = os.getenv("OPENAI_API_KEY") or 'thisIsNotARealKey'
        self.llm_client = OpenAILLMClientWithCache(get_openai_client(openai_api_key))

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
            # 'levallois',  # Not working, duration_in_minutes should be null
            # 'levallois2',  # Not working, duration_in_minutes should be null
            'ndlumieres',
            'carmel',
            # 'stnizier',  # Not working, too long
            'bron',
            'pierresdorees',
            'ste-therese',
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

                fine_tuned_llm_model = 'ft:gpt-4o-2024-08-06:confessio::AHfh95wJ'
                # fine_tuned_llm_model = 'gpt-4o-2024-08-06'
                prompt_template = get_prompt_template()
                schedules_list, error_detail = parse_with_llm(truncated_html, church_desc_by_id,
                                                              fine_tuned_llm_model, prompt_template,
                                                              llm_client=self.llm_client,
                                                              current_year=year)
                self.assertIsNone(error_detail)
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
                llm_model = 'gpt-4o-2024-08-06'
                prompt_template = get_prompt_template()
                schedules_list1, error_detail1 = parse_with_llm(truncated_html1, church_desc_by_id,
                                                                llm_model, prompt_template,
                                                                llm_client=self.llm_client,
                                                                current_year=year)
                self.assertIsNone(error_detail1)
                self.assertIsNotNone(schedules_list1)
                # print(schedules_list1.model_dump_json())

                truncated_html2 = ''.join(lines2)
                schedules_list2, error_detail2 = parse_with_llm(truncated_html2, church_desc_by_id,
                                                                llm_model, prompt_template,
                                                                llm_client=self.llm_client,
                                                                current_year=year)
                self.assertIsNone(error_detail2)
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
