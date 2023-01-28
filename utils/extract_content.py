import json
import string
from unidecode import unidecode
from bs4 import BeautifulSoup
from bs4 import element as el


##################################
# SEARCH FOR CONFESSIONS IN TEXT #
##################################

CONFESSIONS_MENTIONS = [
    'confession',
    'confessions',
    'reconciliation',
]


def normalize_content(content):
    return unidecode(content.lower())


def get_words(content):
    for char in string.punctuation:
        content = content.replace(char, ' ')

    return set(content.split())


def has_confession_mentions(content: string):
    normalized_content = normalize_content(content)
    words = get_words(normalized_content)

    for mention in CONFESSIONS_MENTIONS:
        if mention in words:
            return True

    return False


##############
# PARSE HTML #
##############
TITLES_TAGS = [
    'h3'
]


def group_children_by_section(children_names):
    """Given a list of tags (i.e. ["p", "h1", "p", "p", "h1", "p", "p"],
    returns a list of tuples (title_index, list of children indices)
    example [(None, 0), (1, [2, 3]), (4, [5, 6])]"""
    result = []
    current_title_index = None
    for i, name in enumerate(children_names):
        if name in TITLES_TAGS:
            current_title_index = len(result)
            result.append((i, []))
        elif current_title_index is not None:
            result[current_title_index][1].append(i)
        else:
            result.append((None, [i]))

    return result


def load_from_html(element: el) -> 'ContentTree':
    # We get text and raw_content
    text = element.find(text=True, recursive=False)
    raw_content = element.prettify()

    # We get all children elements
    element_children = list(element.find_all(recursive=False))

    # By analysing children elements tag names we can group children in clusters
    children_tag_names = map(lambda e: e.name, element_children)
    children_by_section = group_children_by_section(children_tag_names)

    children = []
    for title_element, children_elements in children_by_section:
        # we recursively load all children
        children_trees = map(load_from_html, [element_children[i] for i in children_elements])

        if title_element is None:
            # if we don't have any title, we just append all children
            children.extend(children_trees)
            continue

        # if we have a title for this section we load it
        title_tree = load_from_html(element_children[title_element])
        # raw_content is the concatenation of title raw_content and children raw_content's
        raw_content = ''.join(
            [title_tree.raw_content]
            + [child_tree.raw_content for child_tree in children_trees])

        # we append this new element
        children.append(ContentTree(title_tree.text, raw_content, children_trees))

    return ContentTree(text, raw_content, children)


################
# CONTENT TREE #
################

class ContentTree:
    """Tree representation of page content"""

    text: string
    raw_content: string
    children: list['ContentTree']

    def __init__(self, text, raw_content, children):
        self.text = text
        self.raw_content = raw_content
        self.children = children

    @staticmethod
    def _flatten(list_of_lists):
        return [item for sublist in list_of_lists for item in sublist]

    def get_raw_contents_with_confessions(self):
        if self.text is not None and has_confession_mentions(self.text):
            return [self.raw_content]

        return self._flatten(map(ContentTree.get_raw_contents_with_confessions, self.children))

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
    raw_contents_with_confessions = content_tree.get_raw_contents_with_confessions()
    print(json.dumps(raw_contents_with_confessions))
    delimiter = '<br>' if page_type == 'html_page' else '\n'

    return delimiter.join(raw_contents_with_confessions)
