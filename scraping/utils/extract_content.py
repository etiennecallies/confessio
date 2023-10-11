from abc import abstractmethod
from typing import List, Tuple

from scraping.utils.refine_content import refine_confession_content, remove_link_from_html
from scraping.utils.tag_line import Tag, get_tags_with_regex


#############
# INTERFACE #
#############

class BaseTagInterface:
    @abstractmethod
    def get_tags(self, line_without_link: str) -> List[Tag]:
        pass


class RegexOnlyTagInterface(BaseTagInterface):
    def get_tags(self, line_without_link: str) -> List[Tag]:
        return get_tags_with_regex(line_without_link)


######################
# EXTRACT ON REFINED #
######################

MAX_BUFFERING_ATTEMPTS = 2


def split_and_tag(refined_content: str, tag_interface: BaseTagInterface) -> List[Tuple[str, str, List[Tag]]]:
    results = []

    # Split into lines (or <table>)
    for line in refined_content.split('<br>\n'):
        line_without_link = remove_link_from_html(line)

        tags = tag_interface.get_tags(line_without_link)
        results.append((line, line_without_link, tags))

    return results


def prune_lines(lines_and_tags: List[Tuple[str, str, List[Tag]]]):
    results = []
    remaining_buffering_attempts = None
    buffer = []
    date_buffer = []

    for i, (line, line_without_link, tags) in enumerate(lines_and_tags):
        if Tag.SPIRITUAL in tags:
            # We ignore spiritual content
            continue

        if (Tag.SCHEDULE in tags or Tag.PERIOD in tags) \
                and (Tag.CONFESSION in tags or remaining_buffering_attempts is not None):
            # If we found schedules or period and were waiting for it

            # If we found schedules only, we add date_buffer
            if Tag.DATE not in tags:
                results.extend(date_buffer)

            results.extend(buffer)
            buffer = []
            results.append(i)
            date_buffer = []
            remaining_buffering_attempts = MAX_BUFFERING_ATTEMPTS
        elif Tag.CONFESSION in tags \
                or (Tag.DATE in tags and remaining_buffering_attempts is not None):
            # If we found confessions, or date and waiting for it
            buffer.append(i)
            remaining_buffering_attempts = MAX_BUFFERING_ATTEMPTS
        elif remaining_buffering_attempts == 0:
            # If we found nothing and we reached limit without anything
            buffer = []
            remaining_buffering_attempts = None
        elif remaining_buffering_attempts is not None:
            # If we found nothing, and we still have some remaining attempts left
            buffer.append(i)
            remaining_buffering_attempts -= 1
        elif Tag.DATE in tags and Tag.SCHEDULE not in tags:
            # If we found date but not is_schedule we add line to date buffer
            date_buffer.append(i)
        elif Tag.DATE in tags or Tag.SCHEDULE not in tags:
            # If we found both date and schedules OR neither of the two we clear date buffer
            date_buffer = []

    return results


def extract_content(refined_content: str, tag_interface: BaseTagInterface):
    lines_and_tags = split_and_tag(refined_content, tag_interface)
    indices = prune_lines(lines_and_tags)
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
