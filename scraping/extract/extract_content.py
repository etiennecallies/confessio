from abc import abstractmethod
from typing import List, Tuple

from scraping.prune.models import Action
from scraping.prune.prune_lines import get_pruned_lines_indices
from scraping.refine.refine_content import remove_link_from_html
from scraping.extract.tag_line import Tag, get_tags_with_regex


#############
# INTERFACE #
#############

class BaseTagInterface:
    @abstractmethod
    def get_action(self, line_without_link: str) -> Action:
        pass


class DummyTagInterface(BaseTagInterface):
    def get_action(self, line_without_link: str) -> Action:
        return Action.SHOW


class KeyValueInterface(BaseTagInterface):
    def __init__(self, action_per_line_without_link: dict[str, Action]):
        self.action_per_line_without_link = action_per_line_without_link

    def get_action(self, line_without_link: str) -> Action:
        return self.action_per_line_without_link[line_without_link]


######################
# EXTRACT ON REFINED #
######################

def split_and_tag(refined_content: str, tag_interface: BaseTagInterface
                  ) -> List[Tuple[str, str, set[Tag], Action]]:
    results = []

    # Split into lines (or <table>)
    for line in refined_content.split('<br>\n'):
        line_without_link = remove_link_from_html(line)

        tags = get_tags_with_regex(line_without_link)
        action = tag_interface.get_action(line_without_link)
        results.append((line, line_without_link, tags, action))

    return results


def extract_content(refined_content: str, tag_interface: BaseTagInterface):
    lines_and_tags = split_and_tag(refined_content, tag_interface)
    indices = get_pruned_lines_indices(lines_and_tags)
    confession_pieces = list(map(lines_and_tags.__getitem__, indices))
    if not confession_pieces:
        return []

    lines, _lines_without_link, _tags, _action = zip(*confession_pieces)

    return lines
