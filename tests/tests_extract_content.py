import unittest

from utils.extract_content import get_paragraphs


class MyTestCase(unittest.TestCase):
    @staticmethod
    def test_get_paragraphs_fixtures():
        return [
            ('this is content', 'html_page', [])
        ]

    def test_get_paragraphs(self):
        for content, page_type, expected_paragraphs in self.test_get_paragraphs_fixtures():
            with self.subTest():
                paragraphs = get_paragraphs(content, page_type)
                self.assertEqual(paragraphs, expected_paragraphs)


if __name__ == '__main__':
    unittest.main()
