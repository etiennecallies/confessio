import json
import os
import unittest

from scraping.utils.extract_content import ContentTree, is_schedule_description, \
    extract_confession_part_from_content
from scraping.utils.string_search import normalize_content, get_words


class MyTestCase(unittest.TestCase):
    @staticmethod
    def get_paragraphs_fixtures():
        return [
            ('chaville', 'html_page'),
            ('mock1', 'html_page'),
            ('mock2', 'html_page'),
            ('maisons-laffitte', 'html_page'),
            ('ste-jeanne-darc', 'html_page'),
            ('st-jacques-du-haut-pas', 'html_page'),
            ('st-bruno-des-chartreux', 'html_page'),
            ('st-bruno-des-chartreux2', 'html_page'),
            ('amplepuis', 'html_page'),
            ('ntre-dame-de-lassomption', 'html_page'),
            ('st-bonaventure', 'html_page'),
        ]

    def test_get_paragraphs(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for file_name, page_type in self.get_paragraphs_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/paragraphs/{file_name}.html') as f:
                    lines = f.readlines()
                with open(f'{tests_dir}/fixtures/paragraphs/{file_name}.json') as f:
                    expected_paragraphs = json.load(f)
                content = ''.join(lines)
                content_tree = ContentTree.load_content_tree_from_text(content, page_type)
                # print(content_tree)
                raw_contents = content_tree.get_confessions_and_schedules_raw_contents()
                # print(json.dumps(raw_contents))
                self.assertEqual(raw_contents, expected_paragraphs, msg=file_name)

    def test_extract(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for file_name, page_type in self.get_paragraphs_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/paragraphs/{file_name}.html') as f:
                    lines = f.readlines()
                with open(f'{tests_dir}/fixtures/paragraphs/{file_name}.txt') as f:
                    expected_lines = f.readlines()
                content_html = ''.join(lines)
                expected_confession_part = ''.join(expected_lines)

                confession_part = extract_confession_part_from_content(content_html)
                # print(confession_part)

                self.assertEqual(expected_confession_part, confession_part, msg=file_name)

    def test_get_words(self):
        content = 'Bonjour, les confessions sont à 13h le mardi.'
        expected_words = {'Bonjour', 'les', 'confessions', 'sont', 'à', '13h', 'le', 'mardi'}
        words = get_words(content)
        self.assertEqual(words, expected_words)

    def test_normalize_content(self):
        content = 'Bonjour, les confessions sont à 13h le mardi.'
        expected_normalized_content = 'bonjour, les confessions sont a 13h le mardi.'
        normalized_content = normalize_content(content)
        self.assertEqual(normalized_content, expected_normalized_content)

    def test_is_schedule_description(self):
        content = "Le célébrant asssure une permanence de confession avant la messe dans le " \
                  "confessional de la chapelle Saint-Pierre, à droite en entrant dans l'église, " \
                  "de 9h45 à 10h25."
        self.assertTrue(is_schedule_description(content))


if __name__ == '__main__':
    unittest.main()
