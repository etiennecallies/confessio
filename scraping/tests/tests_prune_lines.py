import json
import os
import unittest

from scraping.extract.extract_content import extract_lines_and_indices, ExtractMode
from scraping.extract.split_content import LineAndTag
from scraping.prune.models import Action, Source


class TestPruneLines(unittest.TestCase):
    @staticmethod
    def prune_lines_fixtures():
        return [
            'bron',
            'villeurbanne',
            'chanoineboursier',
            'st-marc',
            'mock',
            'cej',
        ]

    def test_prune_lines(self):
        tests_dir = os.path.dirname(os.path.realpath(__file__))
        for file_name in self.prune_lines_fixtures():
            with self.subTest():
                with open(f'{tests_dir}/fixtures/prune/{file_name}.json') as f:
                    lines_and_tags_as_dict = json.load(f)
                with open(f'{tests_dir}/fixtures/prune/{file_name}.html') as f:
                    lines_output = f.readlines()
                lines_and_tags = []
                for line, line_without_link, tags, action, source in lines_and_tags_as_dict:
                    lines_and_tags.append(LineAndTag(
                        line=line,
                        line_without_link=line_without_link,
                        tags=set(tags),
                        action=Action(action),
                        source=Source(source) if source else None,
                        sentence_uuid=None,
                    ))
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
