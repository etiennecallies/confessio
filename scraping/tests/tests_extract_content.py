import os
import unittest

from scraping.scrape.download_refine_and_extract import get_extracted_html_list
from scraping.utils.string_search import normalize_content, get_words
from scraping.extract.tag_line import is_schedule_description, is_date_description


class MyTestCase(unittest.TestCase):
    @staticmethod
    def get_paragraphs_fixtures():
        return [
            'chaville',
            'mock1',
            'mock2',
            'maisons-laffitte',
            'maisons-laffitte2',
            'ste-jeanne-darc',
            'st-jacques-du-haut-pas',
            'st-bruno-des-chartreux',
            'st-bruno-des-chartreux2',
            'amplepuis',
            'ntre-dame-de-lassomption',
            'ntre-dame-des-lumieres',
            'ntre-dame-des-lumieres2',
            'st-bonaventure',
            'st-nomdejesus',
            'fourviere',
            'cdde',
            'vaise',
            'vaise2',
            'ferreol',
            'smdv',
            'st-alexandre',
            'rambouillet',
            'voisins',
            'houilles',
            'caluire',
            'stebathilde',
            'stbenoit',
            'stgermain',
            'immaculee-conception',
            'sjsc',
            'madeleine',
            'bjmm',
        ]

    def test_extract(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for file_name in self.get_paragraphs_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/extract/{file_name}.html') as f:
                    lines = f.readlines()
                with open(f'{tests_dir}/fixtures/extract/{file_name}.txt') as f:
                    expected_lines = f.readlines()
                content_html = ''.join(lines)
                expected_confession_part = ''.join(expected_lines)

                confession_parts = get_extracted_html_list(content_html)
                confession_part = '\n\n'.join(confession_parts) if confession_parts else None
                # print(confession_part)

                if not expected_confession_part:
                    self.assertIsNone(confession_part, msg=file_name)
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
        contents = [
            "Le célébrant asssure une permanence de confession avant la messe dans le "
            "confessional de la chapelle Saint-Pierre, à droite en entrant dans l'église, "
            "de 9h45 à 10h25.",
            "18:00 - 19:00",
            "Profitons en quel que soit notre âge d’une soirée « Confessions  et  "
            "Adoration »,  le jeudi 21 décembre  de 20 h à 21 h 30 à la Paroisse "
            "Notre Dame Saint-Vincent.",
            "Vendredi 9h: Vauxrenard",
            "Confessions : Les prêtres se rendent disponibles à l’issue des messes.",
            "Les confessions reprendront aux horaires habituels à partir de début septembre.",
            "Fin samedi, mars 30, 2024 - 12: 00",
        ]
        for content in contents:
            with self.subTest():
                self.assertTrue(is_schedule_description(content))

    def test_is_date_description(self):
        contents = [
            "29 Fév",
        ]
        for content in contents:
            with self.subTest():
                self.assertTrue(is_date_description(content))


if __name__ == '__main__':
    unittest.main()
