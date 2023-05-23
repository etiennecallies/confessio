from typing import Optional

from bs4 import BeautifulSoup
from bs4 import element as el
from bs4.element import Comment

from scraping.utils.string_search import has_any_of_words

##################
# LEXICAL SEARCH #
##################

CONFESSIONS_MENTIONS = [
    'confession',
    'confessions',
    'reconciliation',
]

DATES_MENTIONS = [
    'jour',
    'jours',
    'matin',
    'matins',
    'soir',
    'soirs',
    'lundi',
    'lundis',
    'mardi',
    'mardis',
    'mercredi',
    'mercredis',
    'jeudi',
    'jeudis',
    'vendredi',
    'vendredis',
    'samedi',
    'samedis',
    'dimanche',
    'dimanches',
    'janvier',
    'fevrier',
    'mars',
    'avril',
    'mai',
    'juin',
    'juillet',
    'aout',
    'septembre',
    'octobre',
    'novembre',
    'decembre',
    'careme',
    'temps',
    'ordinaire',
]

DATE_REGEX = [
    r'\dh\d\d',
    r'\d\dh\d\d',
]


def has_confession_mentions(content: str):
    return has_any_of_words(content, CONFESSIONS_MENTIONS)


def is_schedule_description(content: str):
    return has_any_of_words(content, DATES_MENTIONS, DATE_REGEX)


##############
# PARSE HTML #
##############


def load_from_html(element: el) -> 'ContentTree':
    # We get text and raw_content
    all_strings = element.find_all(text=lambda t: not isinstance(t, Comment), recursive=False)
    text = ' '.join(all_strings).rstrip()
    raw_content = element.prettify()

    # We get all children elements
    element_children = list(element.find_all(recursive=False))
    children_trees = list(map(load_from_html, element_children))

    return ContentTree(text, raw_content, children_trees)


################
# CONTENT TREE #
################

MAX_CONFESSIONS_BACKWARD_SEARCH_DEPTH = 5
MAX_ELEMENTS_WITHOUT_SCHEDULES = 2


class ContentTree:
    """Tree representation of page content"""

    text: str
    raw_content: str
    children: list['ContentTree']

    def __init__(self, text, raw_content, children):
        self.text = text
        self.raw_content = raw_content
        self.children = children

    def __str__(self):
        children_str = "[]"
        if self.children:
            children_str = "\n".join(map(lambda c: ContentTree._indent(str(c)), self.children))

        return '\n'.join([
            f'text: {self.text}',
            f'raw_content: {self.raw_content}',
            f'children:',
            f'{children_str}'
        ])

    @staticmethod
    def _indent(s: str):
        return '\n'.join([f'    {line}' for line in s.split('\n')])

    def get_confessions_and_schedules_raw_contents(self):
        raw_contents, depth = self._search_for_confessions_and_schedules()

        return raw_contents

    def _search_for_confessions_and_schedules(self):
        """
        :return: a tuple of :
         - relevant list of raw_contents containing confessions and schedules
         - depth of the found confessions if no schedule has been found
        """

        if self.text is not None and has_confession_mentions(self.text):
            # If text has confession mention, we look for schedules description recursively
            if self.has_schedules_description_recursively():
                # If we have both, we return current raw_content
                return [self.raw_content], None
            else:
                # Otherwise we return the depth of confession mentions
                return [], 0

        raw_contents = []
        children_buffer = []
        remaining_attempts_without_schedules = None
        min_confessions_depth = None
        for child in self.children:
            child_raw_contents, confessions_depth = child._search_for_confessions_and_schedules()
            if child_raw_contents:
                # child contains confessions and schedules

                # we flush buffer
                raw_contents.extend(children_buffer)
                children_buffer = []

                if remaining_attempts_without_schedules is not None \
                        and child.has_schedules_description_recursively():
                    # If we were looking for schedules, and if we actually found schedules,
                    # we append entire child
                    raw_contents.append(child.raw_content)
                    # and we are still looking for schedules
                    remaining_attempts_without_schedules = MAX_ELEMENTS_WITHOUT_SCHEDULES
                else:
                    # otherwise we append only the relevant parts
                    raw_contents.extend(child_raw_contents)

            elif confessions_depth is not None \
                    and confessions_depth <= MAX_CONFESSIONS_BACKWARD_SEARCH_DEPTH:
                # child contains confessions but no schedules

                # we update minimum confessions found so far
                if min_confessions_depth is None or confessions_depth < min_confessions_depth:
                    min_confessions_depth = confessions_depth

                # we keep the child in buffer
                children_buffer.append(child.raw_content)
                # and we are now looking for schedules
                remaining_attempts_without_schedules = MAX_ELEMENTS_WITHOUT_SCHEDULES

            elif remaining_attempts_without_schedules is not None:
                # child does not contain confession

                # if we have seen confessions before, we look for schedules
                # until we exhaust the remaining_attempts_without_schedules

                if child.has_schedules_description_recursively():
                    # we found schedules

                    # we flush buffer
                    raw_contents.extend(children_buffer)
                    children_buffer = []

                    # we append the child
                    raw_contents.append(child.raw_content)
                    # and we are still looking for schedules
                    remaining_attempts_without_schedules = MAX_ELEMENTS_WITHOUT_SCHEDULES
                else:
                    # we did not find schedules

                    if remaining_attempts_without_schedules == 0:
                        # we exhausted attempts, we reset all variables
                        children_buffer = []
                        remaining_attempts_without_schedules = None
                        min_confessions_depth = None
                    else:
                        # we still have some attempts
                        remaining_attempts_without_schedules -= 1
                        # we keep the child in buffer, as it can contain other information
                        # than schedules (e.g. location of confessions)
                        children_buffer.append(child.raw_content)

        if raw_contents or min_confessions_depth is None:
            # if there is a complete result (confessions + schedules)
            # or if there is no pending result (confessions recently found)
            final_depth = None
        else:
            # if there is no complete results and one pending result
            final_depth = min_confessions_depth + 1

        return raw_contents, final_depth

    def has_schedules_description_recursively(self):
        if self.text is not None and is_schedule_description(self.text):
            return True

        return any(map(ContentTree.has_schedules_description_recursively, self.children))

    @staticmethod
    def load_content_tree_from_text(content, page_type) -> Optional['ContentTree']:
        if page_type == 'html_page':
            soup = BeautifulSoup(content, 'html.parser')
            body = soup.find('body')
            if body is None:
                return None

            return load_from_html(body)

        # TODO split text into paragraphs (including title of paragraphs)
        return ContentTree('', '', [])


########
# MAIN #
########

def extract_confession_part_from_content(text, page_type):
    content_tree = ContentTree.load_content_tree_from_text(text, page_type)
    if content_tree is None:
        return None

    raw_contents_with_confessions = content_tree.get_confessions_and_schedules_raw_contents()
    if not raw_contents_with_confessions:
        return None

    delimiter = '<br>' if page_type == 'html_page' else '\n'

    return delimiter.join(raw_contents_with_confessions)
