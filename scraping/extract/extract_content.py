from abc import abstractmethod
from typing import Tuple, Optional

from scraping.extract.tag_line import Tag, get_tags_with_regex
from scraping.prune.models import Action, Source
from scraping.prune.prune_lines import get_pruned_lines_indices
from scraping.refine.refine_content import remove_link_from_html


#############
# INTERFACE #
#############

class BaseTagInterface:
    @abstractmethod
    def get_action(self, line_without_link: str) -> tuple[Action, Optional[Source]]:
        pass


class DummyTagInterface(BaseTagInterface):
    def get_action(self, line_without_link: str) -> tuple[Action, Optional[Source]]:
        return Action.SHOW, None


class KeyValueInterface(BaseTagInterface):
    def __init__(self, action_per_line_without_link: dict[str, Action]):
        self.action_per_line_without_link = action_per_line_without_link

    def get_action(self, line_without_link: str) -> tuple[Action, Optional[Source]]:
        return self.action_per_line_without_link[line_without_link], Source.HUMAN


######################
# EXTRACT ON REFINED #
######################

def split_and_tag(refined_content: str, tag_interface: BaseTagInterface
                  ) -> list[Tuple[str, str, set[Tag], Action, Source]]:
    results = []

    # Split into lines (or <table>)
    for line in refined_content.split('<br>\n'):
        line_without_link = remove_link_from_html(line)

        tags = get_tags_with_regex(line_without_link)
        action, source = tag_interface.get_action(line_without_link)
        results.append((line, line_without_link, tags, action, source))

    return results


def get_lines_without_link(refined_content: str) -> list[str]:
    results = []
    for line in refined_content.split('<br>\n'):
        results.append(remove_link_from_html(line))

    return results


def extract_lines_and_indices(lines_and_tags: list[Tuple[str, str, set[Tag], Action, Source]]
                              ) -> list[tuple[list[str], list[int]]]:
    indices = get_pruned_lines_indices(lines_and_tags)

    results = []
    for paragraph_indices in indices:
        paragraph_lines_and_tags = list(map(lines_and_tags.__getitem__, paragraph_indices))
        paragraph_lines = list(map(lambda x: x[0], paragraph_lines_and_tags))
        results.append((paragraph_lines, paragraph_indices))

    return results


def extract_paragraphs_lines_and_indices(refined_content: str, tag_interface: BaseTagInterface
                                         ) -> list[tuple[list[str], list[int]]]:
    lines_and_tags = split_and_tag(refined_content, tag_interface)

    return extract_lines_and_indices(lines_and_tags)
