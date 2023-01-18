import unittest

from utils.extract_content import get_paragraphs, get_words, normalize_content


class MyTestCase(unittest.TestCase):
    @staticmethod
    def test_get_paragraphs_fixtures():
        return [
            ('chaville.txt', 'pdf', [''])
        ]

    def test_get_paragraphs(self):
        for content, page_type, expected_paragraphs in self.test_get_paragraphs_fixtures():
            with self.subTest():
                paragraphs = get_paragraphs(content, page_type)
                self.assertEqual(paragraphs, expected_paragraphs)

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
