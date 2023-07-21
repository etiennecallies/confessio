import re

from bs4 import BeautifulSoup, NavigableString, Comment


##############
# REMOVE IMG #
##############

def remove_img(soup: BeautifulSoup):
    for s in soup.select('img'):
        s.extract()

    for s in soup.select('svg'):
        s.extract()

    return soup


###################
# CONVERT TO TEXT #
###################

def is_table(element):
    return element.name in [
        'table',
    ]


def is_link(element):
    return element.name in [
        'a',
    ]


def is_span(element):
    return element.name in [
        'span',
        'em',
        'strong',
    ]


def is_text(element):
    return isinstance(element, NavigableString) and not isinstance(element, Comment)


def is_comment(element):
    return isinstance(element, Comment)


def get_element_and_text(element):
    return element.contents


def build_text(soup: BeautifulSoup):
    if is_table(soup):
        return soup.prettify()

    if is_link(soup):
        return soup.prettify()

    result = ''
    for element in get_element_and_text(soup):
        if is_span(element):
            result += clean_text(element.text) + ' '
        elif is_text(element):
            result += clean_text(str(element)) + ' '
        elif is_comment(element):
            continue
        else:
            result += build_text(element) + '\n'

    return result


def clean_text(text: str):
    text = re.sub(r'^\s*', '', text)
    text = re.sub(r'([^\n])\n\s*', r'\1\n', text)
    text = re.sub(r'([^ ]) +', r'\1 ', text)
    text = re.sub(r' \n', r'\n', text)
    text = re.sub(r'\s*$', '', text)

    return text


########
# MAIN #
########

def refine_confession_content(content_html):
    if content_html is None:
        return None

    soup = BeautifulSoup(content_html, 'html.parser')
    soup = remove_img(soup)

    text = build_text(soup)
    text = clean_text(text)

    return text
