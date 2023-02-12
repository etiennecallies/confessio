import re
import string

from bs4 import BeautifulSoup, Comment
from bs4 import element as el
from unidecode import unidecode

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


def normalize_content(content):
    return unidecode(content.lower())


def get_words(content):
    for char in string.punctuation:
        content = content.replace(char, ' ')

    return set(content.split())


def has_any_of_words(content: string, lexical_list, regex_list=None):
    normalized_content = normalize_content(content)
    words = get_words(normalized_content)

    for mention in lexical_list:
        if mention in words:
            return True

    if regex_list:
        for regex in regex_list:
            for w in words:
                if re.fullmatch(regex, w):
                    return True

    return False


def has_confession_mentions(content: string):
    return has_any_of_words(content, CONFESSIONS_MENTIONS)


def is_schedule_description(content: string):
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

    text: string
    raw_content: string
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

    def get_confessions_with_schedules(self):
        raw_contents, depth = self._get_raw_contents_with_confessions()

        return raw_contents

    def _get_raw_contents_with_confessions(self):
        if self.text is not None and has_confession_mentions(self.text):
            if self.has_any_schedules_description():
                return [self.raw_content], None
            else:
                return [], 0

        results = []
        children_buffer = []
        remaining_attempts_without_schedules = None
        min_confessions_depth = None
        for child in self.children:
            raw_contents, confessions_depth = child._get_raw_contents_with_confessions()
            if raw_contents:
                # child contains confessions and schedules
                results.extend(children_buffer)
                children_buffer = []

                # We check if we were waiting for schedules
                if remaining_attempts_without_schedules is not None \
                        and child.has_any_schedules_description():
                    results.append(child.raw_content)
                    remaining_attempts_without_schedules = MAX_ELEMENTS_WITHOUT_SCHEDULES
                else:
                    results.extend(raw_contents)
            elif confessions_depth is not None \
                    and confessions_depth <= MAX_CONFESSIONS_BACKWARD_SEARCH_DEPTH:
                # child contains confessions but no schedules
                if min_confessions_depth is None or confessions_depth < min_confessions_depth:
                    min_confessions_depth = confessions_depth
                children_buffer.append(child.raw_content)
                remaining_attempts_without_schedules = MAX_ELEMENTS_WITHOUT_SCHEDULES
            elif remaining_attempts_without_schedules is not None:
                # if we have seen confessions before, we look for schedules
                # until we exhaust the remaining_attempts_without_schedules
                if child.has_any_schedules_description():
                    results.extend(children_buffer)
                    children_buffer = []
                    results.append(child.raw_content)
                    remaining_attempts_without_schedules = MAX_ELEMENTS_WITHOUT_SCHEDULES
                else:
                    if remaining_attempts_without_schedules == 0:
                        children_buffer = []
                        remaining_attempts_without_schedules = None
                        min_confessions_depth = None
                    else:
                        remaining_attempts_without_schedules -= 1
                        children_buffer.append(child.raw_content)

        # if there is no results (confessions + schedules), and confessions only has been found
        # We return min depth of confessions found plus one
        final_depth = min_confessions_depth + 1 \
            if min_confessions_depth is not None and not results else None
        return results, final_depth

    def has_any_schedules_description(self):
        if self.text is not None and is_schedule_description(self.text):
            return True

        return any(map(ContentTree.has_any_schedules_description, self.children))

    @staticmethod
    def load_content_tree_from_text(content, page_type) -> 'ContentTree':
        if page_type == 'html_page':
            soup = BeautifulSoup(content, 'html.parser')
            body = soup.find('body')

            return load_from_html(body)

        # TODO split text into paragraphs (including title of paragraphs)
        return ContentTree('', '', [])


########
# MAIN #
########

def extract_confession_part_from_content(text, page_type):
    content_tree = ContentTree.load_content_tree_from_text(text, page_type)
    raw_contents_with_confessions = content_tree.get_confessions_with_schedules()
    delimiter = '<br>' if page_type == 'html_page' else '\n'

    return delimiter.join(raw_contents_with_confessions)
