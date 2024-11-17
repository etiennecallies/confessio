from abc import abstractmethod
from enum import Enum
from typing import Tuple, Optional

from scraping.extract.tag_line import Tag, get_tags_with_regex
from scraping.prune.models import Action, Source
from scraping.prune.prune_lines import get_pruned_lines_indices
from scraping.refine.refine_content import remove_link_from_html


#############
# INTERFACE #
#############

class BaseActionInterface:
    @abstractmethod
    def get_action(self, line_without_link: str) -> tuple[Action, Optional[Source]]:
        pass


class DummyActionInterface(BaseActionInterface):
    def get_action(self, line_without_link: str) -> tuple[Action, Optional[Source]]:
        return Action.SHOW, None


class KeyValueInterface(BaseActionInterface):
    def __init__(self, action_per_line_without_link: dict[str, Action]):
        self.action_per_line_without_link = action_per_line_without_link

    def get_action(self, line_without_link: str) -> tuple[Action, Optional[Source]]:
        return self.action_per_line_without_link[line_without_link], Source.HUMAN


###########
# EXTRACT #
###########

class ExtractMode(str, Enum):
    EXTRACT = 'extract'
    PRUNE = 'prune'


def split_and_tag(refined_content: str, action_interface: BaseActionInterface
                  ) -> list[Tuple[str, str, set[Tag], Action, Source]]:
    results = []

    # Split into lines (or <table>)
    for line in refined_content.split('<br>\n'):
        line_without_link = remove_link_from_html(line)

        tags = get_tags_with_regex(line_without_link)
        action, source = action_interface.get_action(line_without_link)
        results.append((line, line_without_link, tags, action, source))

    return results


def extract_lines_and_indices(lines_and_tags: list[Tuple[str, str, set[Tag], Action, Source]],
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
        paragraph_lines = list(map(lambda x: x[0], paragraph_lines_and_tags))
        results.append((paragraph_lines, paragraph_indices))

    return results


def extract_paragraphs_lines_and_indices(refined_content: str,
                                         action_interface: BaseActionInterface,
                                         extract_mode: ExtractMode
                                         ) -> list[tuple[list[str], list[int]]]:
    lines_and_tags = split_and_tag(refined_content, action_interface)

    return extract_lines_and_indices(lines_and_tags, extract_mode)
