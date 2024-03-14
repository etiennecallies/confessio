import os
import unittest

from scraping.utils.extract_content import extract_confession_part_from_content
from scraping.utils.string_search import normalize_content, get_words
from scraping.utils.tag_line import is_schedule_description


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
            ('ntre-dame-des-lumieres', 'html_page'),
            ('ntre-dame-des-lumieres2', 'html_page'),
            ('st-bonaventure', 'html_page'),
            ('st-nomdejesus', 'html_page'),
            ('fourviere', 'html_page'),
            ('cdde', 'html_page'),
            ('vaise', 'html_page'),
            ('ferreol', 'html_page'),
        ]

    def test_extract(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for file_name, page_type in self.get_paragraphs_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/extract/{file_name}.html') as f:
                    lines = f.readlines()
                with open(f'{tests_dir}/fixtures/extract/{file_name}.txt') as f:
                    expected_lines = f.readlines()
                content_html = ''.join(lines)
                expected_confession_part = ''.join(expected_lines)

                confession_part = extract_confession_part_from_content(content_html)
                # print(confession_part)

                if not expected_confession_part:
                    self.assertIsNone(confession_part)
                else:
                    self.maxDiff = None
                    self.assertEqual(expected_confession_part, confession_part, msg=file_name)

    def test_get_words(self):
        content = 'Bonjour, les confessions sont à 13h le mardi.'
        expected_words = ['Bonjour', 'les', 'confessions', 'sont', 'à', '13h', 'le', 'mardi']
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

    def test_is_schedule_description_hour(self):
        content = "18:00 - 19:00"
        self.assertTrue(is_schedule_description(content))

    def test_is_schedule_description_spcae(self):
        content = "Profitons en quel que soit notre âge d’une soirée « Confessions  et  " \
                  "Adoration »,  le jeudi 21 décembre  de 20 h à 21 h 30 à la Paroisse " \
                  "Notre Dame Saint-Vincent."
        self.assertTrue(is_schedule_description(content))


if __name__ == '__main__':
    unittest.main()
