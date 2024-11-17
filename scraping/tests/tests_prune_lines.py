import json
import os
import unittest

from scraping.extract.extract_content import extract_lines_and_indices


class TestPruneLines(unittest.TestCase):
    @staticmethod
    def prune_lines_fixtures():
        return [
            'bron',
            'villeurbanne',
            'chanoineboursier',
            'st-marc',
        ]

    def test_prune_lines(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for file_name in self.prune_lines_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/prune/{file_name}.json') as f:
                    lines_and_tags = json.load(f)
                with open(f'{tests_dir}/fixtures/prune/{file_name}.html') as f:
                    lines_output = f.readlines()
                expected_output = ''.join(lines_output)
                paragraphs = extract_lines_and_indices(lines_and_tags)
                paragraph_outputs = []
                for paragraph_lines, paragraph_indices in paragraphs:
                    paragraph_outputs.append('<br>\n'.join(paragraph_lines))
                output = '\n\n'.join(paragraph_outputs)
                # print(output)
                self.maxDiff = None
                self.assertEqual(expected_output, output, file_name)


if __name__ == '__main__':
    unittest.main()
