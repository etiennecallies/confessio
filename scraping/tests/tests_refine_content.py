import os
import unittest

from scraping.utils.refine_content import refine_confession_content


class TestExtractLinks(unittest.TestCase):
    @staticmethod
    def parse_content_links_fixtures():
        return [
            'val-de-saone',
            'val-de-saone2',
            'laredemption-st-joseph',
            'st-georges',
            'st-bonaventure',
            'bellecombe',
        ]

    def test_parse_content_links(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for file_name in self.parse_content_links_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/refine/{file_name}-input.html') as f:
                    lines_input = f.readlines()
                with open(f'{tests_dir}/fixtures/refine/{file_name}-output.html') as f:
                    lines_output = f.readlines()
                input_html = ''.join(lines_input)
                expected_output = ''.join(lines_output)
                output = refine_confession_content(input_html)
                # print(output)
                self.assertEqual(expected_output, output)


if __name__ == '__main__':
    unittest.main()
