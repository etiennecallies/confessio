import asyncio
import json
import os
import unittest

from scraping.download.download_content import get_domain
from scraping.crawl.extract_links import parse_content_links


class TestExtractLinks(unittest.TestCase):
    @staticmethod
    def parse_content_links_fixtures():
        return [
            ('https://www.eglise-saintgermaindespres.fr/', 'st-germain-des-pres'),
            ('https://paroissesaintbruno.pagesperso-orange.fr/', 'st-bruno-des-chartreux'),
            ('https://saintleusaintgilles.fr/', 'st-leu-st-gilles'),
            ('http://paroisse.ndchoisille.free.fr/', 'ndchoisille'),
        ]

    def test_parse_content_links(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for home_url, file_name in self.parse_content_links_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/urls/{file_name}.html') as f:
                    lines = f.readlines()
                with open(f'{tests_dir}/fixtures/urls/{file_name}.json') as f:
                    expected_links = json.load(f)
                content = ''.join(lines)
                links = asyncio.run(parse_content_links(content, home_url, {get_domain(home_url)},
                                                        set(), {}, set()))
                # print(json.dumps(list(links), indent=2))
                self.assertSetEqual(links, set(expected_links), f'Failed for {file_name}')


if __name__ == '__main__':
    unittest.main()
