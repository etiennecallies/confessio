import json
import os
import unittest

from scheduling.workflows.pruning.extract_interface import ExtractMode
from scheduling.workflows.pruning.extract_v2.extract_content import extract_lines_and_indices
from scheduling.workflows.pruning.extract_v2.split_content import LineAndTagV2


class TestPruneLines(unittest.TestCase):
    @staticmethod
    def prune_lines_fixtures():
        return [
            'colombe',
            'teresa',
            'paimpol',
            'teresa2',
        ]

    def test_prune_lines(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for file_name in self.prune_lines_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/prune_v2/{file_name}.json') as f:
                    lines_and_tags_as_dict = json.load(f)
                with open(f'{tests_dir}/fixtures/prune_v2/{file_name}.html') as f:
                    lines_output = f.readlines()
                lines_and_tags = []
                for d in lines_and_tags_as_dict:
                    lines_and_tags.append(LineAndTagV2(**d))
                expected_output = ''.join(lines_output)

                paragraphs = extract_lines_and_indices(lines_and_tags, ExtractMode.PRUNE)
                paragraph_outputs = []
                for paragraph_lines, paragraph_indices in paragraphs:
                    paragraph_outputs.append('<br>\n'.join(paragraph_lines))
                output = '\n\n'.join(paragraph_outputs)
                # print(output)
                self.maxDiff = None
                self.assertEqual(expected_output, output, file_name)


if __name__ == '__main__':
    unittest.main()
