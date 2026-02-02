import json
import os
import unittest

from crawling.workflows.crawl.extract_widgets import BaseWidget, extract_widgets


class TestExtractLinks(unittest.TestCase):
    @staticmethod
    def widgets_fixtures():
        return [
            'ancenis',
        ]

    def test_extract_widgets(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for file_name in self.widgets_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/widgets/{file_name}.html') as f:
                    lines = f.readlines()
                with open(f'{tests_dir}/fixtures/widgets/{file_name}.json') as f:
                    expected_result = [BaseWidget(**w) for w in json.load(f)]
                content = ''.join(lines)
                result = extract_widgets(content)
                # print(json.dumps(list(result), indent=2))
                self.assertListEqual(result, expected_result, f'Failed for {file_name}')


if __name__ == '__main__':
    unittest.main()
