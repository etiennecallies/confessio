import re

from bs4 import BeautifulSoup, NavigableString, Comment, ProcessingInstruction


##############
# REMOVE IMG #
##############

def remove_img(soup: BeautifulSoup):
    for s in soup.select('img'):
        s.extract()

    for s in soup.select('svg'):
        s.extract()

    return soup


def remove_script(soup: BeautifulSoup):
    for s in soup.select('script'):
        s.extract()

    for s in soup.select('style'):
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
        'u',
        'sup',
        'b',
    ]


def is_text(element):
    return isinstance(element, NavigableString) and not is_comment(element)


def is_comment(element):
    return isinstance(element, Comment) or isinstance(element, ProcessingInstruction)


def get_element_and_text(element):
    return element.contents


def clear_formatting(element: BeautifulSoup):
    # remove all attributes except "href"
    attrs = dict(element.attrs)
    for attr in attrs:
        if attr not in ['href']:
            del element.attrs[attr]

    # keeping only text as html
    element.string = element.getText()


def build_text(soup: BeautifulSoup):
    if is_table(soup):
        return soup.prettify()

    results = []
    for element in get_element_and_text(soup):
        if is_span(element):
            results.append(clean_text(element.text))
        elif is_text(element):
            results.append(clean_text(str(element)))
        elif is_comment(element):
            continue
        elif is_link(element):
            clear_formatting(element)
            results.append(flatten_string(element.prettify()))
        else:
            text = build_text(element)
            if text:
                results.append('<br>\n' + text + '<br>\n')

    results = filter(lambda s: len(s) > 0, results)

    return ' '.join(results)


def clean_text(text: str):
    text = text.replace('\u200b', '')
    text = re.sub(r'^\s*', '', text)
    text = re.sub(r'( )+', r' ', text)
    text = re.sub(r'\n ', r'\n', text)
    text = re.sub(r' \n', r'\n', text)
    text = re.sub(r'(\n)+', r'\n', text)
    text = re.sub(r'\s*$', '', text)

    return text


def flatten_string(text: str):
    text = re.sub(r'^\s*', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s*$', '', text)

    return text


def clean_paragraph(text: str):
    text = re.sub(r'<br> ', r'<br>', text)
    text = re.sub(r' <br>', r'<br>', text)
    text = re.sub(r'(<br>\n)+', r'<br>\n', text)
    text = re.sub(r'^<br>(\n)?', '', text)
    text = re.sub(r'<br>(\n)?$', '', text)

    return text


###############
# REMOVE LINK #
###############

def remove_link_from_html(html: str) -> str:
    return re.sub('href="[^"]+"', '', html)

########
# MAIN #
########

def refine_confession_content(content_html):
    if content_html is None:
        return None

    soup = BeautifulSoup(content_html, 'html.parser')
    soup = remove_img(soup)
    soup = remove_script(soup)

    text = build_text(soup)
    text = clean_paragraph(text)

    return text
