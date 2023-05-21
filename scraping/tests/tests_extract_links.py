import json
import os
import unittest

from scraping.utils.extract_links import parse_content_links


class TestExtractLinks(unittest.TestCase):
    @staticmethod
    def parse_content_links_fixtures():
        return [
            ('https://www.eglise-saintgermaindespres.fr/', 'st-germain-des-pres'),
        ]

    def test_parse_content_links(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for home_url, file_name in self.parse_content_links_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/urls/{file_name}.html') as f:
                    lines = f.readlines()
                with open(f'{tests_dir}/fixtures/urls/{file_name}.json') as f:
                    expected_links = json.load(f)
                content = '\n'.join(lines)
                links = parse_content_links(content, home_url)
                self.assertSetEqual(links, set(expected_links))


if __name__ == '__main__':
    unittest.main()