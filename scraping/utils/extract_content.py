from abc import abstractmethod
from typing import List, Tuple, Set

from scraping.utils.prune_lines import get_pruned_lines_indices
from scraping.utils.refine_content import refine_confession_content, remove_link_from_html
from scraping.utils.tag_line import Tag, get_tags_with_regex


#############
# INTERFACE #
#############

class BaseTagInterface:
    @abstractmethod
    def get_tags(self, line_without_link: str) -> Set[Tag]:
        pass


class RegexOnlyTagInterface(BaseTagInterface):
    def get_tags(self, line_without_link: str) -> Set[Tag]:
        return get_tags_with_regex(line_without_link)


######################
# EXTRACT ON REFINED #
######################

def split_and_tag(refined_content: str, tag_interface: BaseTagInterface
                  ) -> List[Tuple[str, str, Set[Tag]]]:
    results = []

    # Split into lines (or <table>)
    for line in refined_content.split('<br>\n'):
        line_without_link = remove_link_from_html(line)

        tags = tag_interface.get_tags(line_without_link)
        results.append((line, line_without_link, tags))

    return results


def extract_content(refined_content: str, tag_interface: BaseTagInterface):
    lines_and_tags = split_and_tag(refined_content, tag_interface)
    indices = get_pruned_lines_indices(lines_and_tags)
    confession_pieces = list(map(lines_and_tags.__getitem__, indices))
    if not confession_pieces:
        return []

    lines, _lines_without_link, _tags = zip(*confession_pieces)

    return lines


########
# MAIN #
########

def extract_confession_part_from_content(html_content):
    refined_content = refine_confession_content(html_content)
    if refined_content is None:
        return None

    paragraphs = extract_content(refined_content, RegexOnlyTagInterface())
    if not paragraphs:
        return None

    return '<br>\n'.join(paragraphs)
