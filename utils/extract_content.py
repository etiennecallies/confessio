import string
from unidecode import unidecode
from bs4 import BeautifulSoup, PageElement

CONFESSIONS_MENTIONS = [
    'confession',
    'confessions',
    'reconciliation',
]


def flatten(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]


class ContentTree:
    text: string
    raw_content: string
    children: list['ContentTree']

    def __init__(self, text, raw_content, children):
        self.text = text
        self.raw_content = raw_content
        self.children = children

    def search_for_confessions(self):
        if self.text is not None and has_confession_mentions(self.text):
            return [self.raw_content]

        return flatten(map(ContentTree.search_for_confessions, self.children))


def load_from_html(element: PageElement) -> ContentTree:
    text = element.find(text=True, recursive=False)
    raw_content = element.prettify()

    if element.name in ['h3']:
        return ContentTree(text, raw_content, load_from_html(element.next_siblings))

    children_names = map(lambda e: e.name, element.find_all(recursive=False))
    children_indices_lists = split_children(children_names)
    element_children = list(element.find_all(recursive=False))
    for title_element, children_elements in children_indices_lists:

        # TODO finish this

        title_tree = load_from_html(element_children[title_element])
        children_tree = map(load_from_html, [element_children[i] for i in children_elements])
        raw_content = title_tree.raw_content + ''.join(
            [child_tree.raw_content for child_tree in children_tree])
        return ContentTree(title_tree.text, raw_content, children_tree)


def get_content_tree(content, page_type) -> ContentTree:
    if page_type == 'html_page':
        soup = BeautifulSoup(content, 'html.parser')
        body = soup.find('body')

        return load_from_html(body)

    # TODO split text into paragraphs (including title of paragraphs)
    return ContentTree('', '', [])


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


def extract_confession_part_from_content(content, page_type):
    content_tree = get_content_tree(content, page_type)
    trees_with_confessions = content_tree.search_for_confessions()
    delimiter = '<br>' if page_type == 'html_page' else '\n'

    return delimiter.join(trees_with_confessions)


if __name__ == '__main__':
    with open('../tests/fixtures/chaville.txt') as f:
        lines = f.readlines()
    content = '\n'.join(lines)
    print(extract_confession_part_from_content(content, page_type='html_page'))
