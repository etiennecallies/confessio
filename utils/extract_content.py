import string

from bs4 import BeautifulSoup
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
]


def normalize_content(content):
    return unidecode(content.lower())


def get_words(content):
    for char in string.punctuation:
        content = content.replace(char, ' ')

    return set(content.split())


def has_any_of_words(content: string, lexical_list):
    normalized_content = normalize_content(content)
    words = get_words(normalized_content)

    for mention in lexical_list:
        if mention in words:
            return True

    return False


def has_confession_mentions(content: string):
    return has_any_of_words(content, CONFESSIONS_MENTIONS)


def is_schedule_description(content: string):
    return has_any_of_words(content, DATES_MENTIONS)


##############
# PARSE HTML #
##############


def load_from_html(element: el) -> 'ContentTree':
    # We get text and raw_content
    text = element.find(text=True, recursive=False)
    raw_content = element.prettify()

    # We get all children elements
    element_children = list(element.find_all(recursive=False))
    children_trees = list(map(load_from_html, element_children))

    return ContentTree(text, raw_content, children_trees)


################
# CONTENT TREE #
################

MAX_CONFESSIONS_BACKWARD_SEARCH_DEPTH = 1
MAX_ELEMENTS_WITHOUT_SCHEDULES = 1


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
        remaining_elements = None
        min_depth = None
        for child in self.children:
            raw_contents, depth = child._get_raw_contents_with_confessions()
            if raw_contents:
                # child contains confessions and schedules
                results.extend(children_buffer)
                children_buffer = []
                results.extend(raw_contents)
            elif depth is not None and depth <= MAX_CONFESSIONS_BACKWARD_SEARCH_DEPTH:
                # child contains confessions but no schedules
                if min_depth is None or depth < min_depth:
                    min_depth = depth
                children_buffer.append(child.raw_content)
                remaining_elements = MAX_ELEMENTS_WITHOUT_SCHEDULES
            elif remaining_elements is not None:
                # if we have seen confessions before, we look for schedules
                # until we exhaust the remaining_elements
                if child.has_any_schedules_description():
                    results.extend(children_buffer)
                    children_buffer = []
                    results.append(child.raw_content)
                    remaining_elements = MAX_ELEMENTS_WITHOUT_SCHEDULES
                else:
                    remaining_elements -= 1
                    if remaining_elements == 0:
                        children_buffer = []
                        remaining_elements = None
                    else:
                        children_buffer.append(child.raw_content)

        return results, min_depth + 1 if min_depth is not None else None

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
    # print(json.dumps(raw_contents_with_confessions))  # TODO create command to insert it in fixtures ?
    delimiter = '<br>' if page_type == 'html_page' else '\n'

    return delimiter.join(raw_contents_with_confessions)
