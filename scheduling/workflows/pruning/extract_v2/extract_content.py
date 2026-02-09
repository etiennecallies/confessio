from scheduling.workflows.pruning.extract_interface import ExtractMode, BaseExtractInterface
from scheduling.workflows.pruning.extract_v2.prune_lines_v2 import get_pruned_lines_indices_v2
from scheduling.workflows.pruning.extract_v2.qualify_line_interfaces import BaseQualifyLineInterface
from scheduling.workflows.pruning.extract_v2.split_content import LineAndTagV2, split_and_tag_v2


###########
# EXTRACT #
###########

def extract_lines_and_indices(lines_and_tags: list[LineAndTagV2],
                              extract_mode: ExtractMode
                              ) -> list[tuple[list[str], list[int]]]:
    indices_list = get_pruned_lines_indices_v2(lines_and_tags)

    if extract_mode == ExtractMode.PRUNE:
        paragraphes_indices = [sum(indices_list, [])] if indices_list else []
    elif extract_mode == ExtractMode.EXTRACT:
        paragraphes_indices = [list(range(indices[0], indices[-1] + 1)) for indices in indices_list]
    else:
        raise ValueError(f'Unknown extract_mode: {extract_mode}')

    results = []
    for paragraph_indices in paragraphes_indices:
        paragraph_lines_and_tags = list(map(lines_and_tags.__getitem__, paragraph_indices))
        paragraph_lines = list(map(lambda lt: lt.line, paragraph_lines_and_tags))
        results.append((paragraph_lines, paragraph_indices))

    return results


def extract_paragraphs_lines_and_indices_v2(refined_content: str,
                                            qualify_line_interface: BaseQualifyLineInterface,
                                            extract_mode: ExtractMode
                                            ) -> list[tuple[list[str], list[int]]]:
    lines_and_tags = split_and_tag_v2(refined_content, qualify_line_interface)

    return extract_lines_and_indices(lines_and_tags, extract_mode)


class ExtractV2Interface(BaseExtractInterface):
    def __init__(self, qualify_line_interface: BaseQualifyLineInterface):
        self.qualify_line_interface = qualify_line_interface

    def extract_paragraphs_lines_and_indices(self, refined_content: str,
                                             extract_mode: ExtractMode
                                             ) -> list[tuple[list[str], list[int]]]:
        return extract_paragraphs_lines_and_indices_v2(refined_content,
                                                       self.qualify_line_interface,
                                                       extract_mode)
