import json
import os
import unittest

from utils.extract_content import get_words, normalize_content, ContentTree


class MyTestCase(unittest.TestCase):
    @staticmethod
    def test_get_paragraphs_fixtures():
        return [
            ('chaville.txt', 'html_page', 'chaville.json')
        ]

    def test_get_paragraphs(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for content_file_name, page_type, expected_json_file in self.test_get_paragraphs_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/{content_file_name}') as f:
                    lines = f.readlines()
                with open(f'{tests_dir}/fixtures/{expected_json_file}') as f:
                    expected_paragraphs = json.load(f)
                content = '\n'.join(lines)
                content_tree = ContentTree.load_content_tree_from_text(content, page_type)
                raw_contents_with_confessions = content_tree.get_raw_contents_with_confessions()
                self.assertEqual(raw_contents_with_confessions, expected_paragraphs)

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


if __name__ == '__main__':
    unittest.main()
