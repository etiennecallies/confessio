import os
import unittest

from scraping.refine.refine_content import refine_confession_content


class TestExtractLinks(unittest.TestCase):
    @staticmethod
    def refine_content_fixtures():
        return [
            'val-de-saone',
            'val-de-saone2',
            'laredemption-st-joseph',
            'ntre-dame-des-lumieres',
            'st-georges',
            'st-nizier',
            'st-bonaventure',
            'st-louis-antin',
            'bellecombe',
            'vaise',
            'paroisseoullins',
            'tassin',
            'mornantais',
            'montesson',
            'bellecombe2',
            'pouilly',
            'st-roch',
            'cannes',
        ]

    def test_refine_content(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for file_name in self.refine_content_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/refine/{file_name}-input.html') as f:
                    lines_input = f.readlines()
                with open(f'{tests_dir}/fixtures/refine/{file_name}-output.html') as f:
                    lines_output = f.readlines()
                input_html = ''.join(lines_input)
                expected_output = ''.join(lines_output)

                # Test that input produces expected output
                output = refine_confession_content(input_html)
                # print(output)
                self.maxDiff = None
                self.assertEqual(expected_output, output, file_name)

                # Idempotent test
                output_on_output = refine_confession_content(expected_output)
                # print(output_on_output)
                self.maxDiff = None
                self.assertEqual(expected_output, output_on_output, file_name)


if __name__ == '__main__':
    unittest.main()
