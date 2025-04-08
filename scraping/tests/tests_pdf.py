import os
import unittest

from scraping.refine.pdf_utils import extract_text_from_pdf_file
from scraping.scrape.download_refine_and_extract import get_extracted_html_list


class MyTestCase(unittest.TestCase):
    @staticmethod
    def get_paragraphs_fixtures():
        return [
            'randol',
        ]

    def test_extract_pdf(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for file_name in self.get_paragraphs_fixtures():
            with self.subTest():
                pdf_file_name = f'{tests_dir}/fixtures/pdf/{file_name}.pdf'
                content_html = extract_text_from_pdf_file(pdf_file_name)
                with open(f'{tests_dir}/fixtures/pdf/{file_name}.txt') as f:
                    expected_lines = f.readlines()
                expected_confession_part = ''.join(expected_lines)

                confession_parts = get_extracted_html_list(content_html)
                confession_part = '\n\n'.join(confession_parts) if confession_parts else None
                # print(confession_part)

                if not expected_confession_part:
                    self.assertIsNone(confession_part, msg=file_name)
                else:
                    self.maxDiff = None
                    self.assertEqual(expected_confession_part, confession_part, msg=file_name)


if __name__ == '__main__':
    unittest.main()
