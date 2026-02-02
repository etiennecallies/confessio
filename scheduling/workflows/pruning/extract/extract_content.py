from scheduling.workflows.pruning.extract.extract_interface import ExtractMode, BaseExtractInterface
from scheduling.workflows.pruning.extract.split_content import LineAndTag, split_and_tag
from scheduling.workflows.pruning.action_interfaces import BaseActionInterface
from scheduling.workflows.pruning.prune_lines import get_pruned_lines_indices


###########
# EXTRACT #
###########


def extract_lines_and_indices(lines_and_tags: list[LineAndTag],
                              extract_mode: ExtractMode
                              ) -> list[tuple[list[str], list[int]]]:
    indices_list = get_pruned_lines_indices(lines_and_tags)

    results = []
    for indices in indices_list:
        if extract_mode == ExtractMode.PRUNE:
            paragraph_indices = indices
        elif extract_mode == ExtractMode.EXTRACT:
            paragraph_indices = list(range(indices[0], indices[-1] + 1))
        else:
            raise ValueError(f'Unknown extract_mode: {extract_mode}')

        paragraph_lines_and_tags = list(map(lines_and_tags.__getitem__, paragraph_indices))
        paragraph_lines = list(map(lambda lt: lt.line, paragraph_lines_and_tags))
        results.append((paragraph_lines, paragraph_indices))

    return results


def extract_paragraphs_lines_and_indices(refined_content: str,
                                         action_interface: BaseActionInterface,
                                         extract_mode: ExtractMode
                                         ) -> list[tuple[list[str], list[int]]]:
    lines_and_tags = split_and_tag(refined_content, action_interface)

    return extract_lines_and_indices(lines_and_tags, extract_mode)


class ExtractV1Interface(BaseExtractInterface):
    def __init__(self, action_interface: BaseActionInterface):
        self.action_interface = action_interface

    def extract_paragraphs_lines_and_indices(self, refined_content: str,
                                             extract_mode: ExtractMode
                                             ) -> list[tuple[list[str], list[int]]]:
        return extract_paragraphs_lines_and_indices(refined_content,
                                                    self.action_interface,
                                                    extract_mode)
