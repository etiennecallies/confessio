import json
import os
import unittest

from scraping.prune.prune_lines import get_pruned_lines_indices


class TestPruneLines(unittest.TestCase):
    @staticmethod
    def prune_lines_fixtures():
        return [
            'bron',
        ]

    def test_prune_lines(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for file_name in self.prune_lines_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/prune/{file_name}-input.json') as f:
                    lines_and_tags = json.load(f)
                with open(f'{tests_dir}/fixtures/prune/{file_name}-output.html') as f:
                    lines_output = f.readlines()
                expected_output = ''.join(lines_output)
                kept_indices = get_pruned_lines_indices(lines_and_tags)
                confession_pieces = list(map(lines_and_tags.__getitem__, kept_indices))
                paragraphs = list(map(lambda x: x[0], confession_pieces))
                output = '<br>\n'.join(paragraphs)
                # print(output)
                self.maxDiff = None
                self.assertEqual(expected_output, output, file_name)


if __name__ == '__main__':
    unittest.main()
