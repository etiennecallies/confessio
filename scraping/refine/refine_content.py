import re
import string
import warnings
from typing import Optional

from bs4 import BeautifulSoup, NavigableString, Comment, ProcessingInstruction, \
    MarkupResemblesLocatorWarning, PageElement

from scraping.refine.detect_calendar import is_calendar_item
from scraping.utils.string_utils import is_below_byte_limit


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


##################
# TABLE CLEANING #
##################

def is_table(element):
    if element.name in [
        'table',
    ]:
        if 'mailpoet' in element.prettify():
            # mailpoet is a newsletter framework that uses <table> for its structure
            # https://www.paroissesferreoletozanam.fr/?mailpoet_router=&endpoint=view_in_browser&action=view&data=WzExMSwiMmZkYjYyM2UzZTUwIiwwLDAsMTY3LDFd
            return False

        if not is_below_byte_limit(clean_text(element.text)):
            # Table content is too long, we split it
            return False

        return True

    return False


def clear_formatting(element: PageElement):
    if element.name in ['font', 'strong', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        element.name = 'span'

    if hasattr(element, 'attrs'):
        attrs = dict(element.attrs)
        for attr in attrs:
            if attr in ['id', 'class', 'style', 'href', 'width', 'border'] \
                    or attr.startswith('data-'):
                del element.attrs[attr]


def clear_table_formatting(element: BeautifulSoup):
    clear_formatting(element)

    for el in element.descendants:
        clear_formatting(el)


def rec_prettify(element: BeautifulSoup):
    last_prettified_html = None
    prettified_html = element.prettify()

    max_iterations = 100

    while last_prettified_html is None or prettified_html != last_prettified_html:
        prettified_bs4 = BeautifulSoup(prettified_html, 'html.parser')
        last_prettified_html = prettified_html
        prettified_html = prettified_bs4.prettify()

        max_iterations -= 1
        if max_iterations <= 0:
            raise ValueError('too many prettify')

    return prettified_html


def refine_table_or_calendar(soup: BeautifulSoup):
    clear_table_formatting(soup)
    return rec_prettify(soup)


##################
# TEXT CLEANING #
##################


def clear_link_formatting(element: BeautifulSoup):
    # remove all attributes except "href"
    attrs = dict(element.attrs)
    for attr in attrs:
        if attr not in ['href']:
            del element.attrs[attr]

    # keeping only text as html
    element.string = ' '.join(element.stripped_strings)


def flatten_string(text: str):
    text = re.sub(r'^\s*', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s*$', '', text)

    return text


def clean_text(text: str):
    text = text.replace("", "")
    text = text.replace('\u200b', '')
    text = text.replace('\u00A0', ' ')  # replace non-breaking space by space
    text = re.sub(r'^\s*', '', text)
    text = re.sub(r'( )+', r' ', text)
    text = re.sub(r'\n ', r'\n', text)
    text = re.sub(r' \n', r'\n', text)
    text = re.sub(r'(\n)+', r'\n', text)
    text = re.sub(r'\s*$', '', text)
    text = text.strip()

    return text


def contains_char_or_digits(text):
    # If text contains character NUL, it's a good hint that this line is not proper text
    if '\x00' in text:
        return False

    char_or_digits = set(string.ascii_letters + string.digits)
    for t in remove_link_from_html(text):
        if t in char_or_digits:
            return True
    return False


def line_is_suitable(text: str):
    return contains_char_or_digits(text) and is_below_byte_limit(remove_link_from_html(text))


def clean_paragraph(text: str):
    text = re.sub(r'<br> ', r'<br>', text)
    text = re.sub(r' <br>', r'<br>', text)
    text = re.sub(r'<br>\n +', r'<br>\n', text)
    text = re.sub(r'(<br>\n)+', r'<br>\n', text)
    text = re.sub(r'\n<br>', r'<br>', text)
    text = re.sub(r'^<br>(\n)?', '', text)
    text = re.sub(r'<br>(\n)?$', '', text)
    text = re.sub(r'(\n)+$', '', text)

    # Remove non suitable lines
    text = '<br>\n'.join(filter(line_is_suitable, text.split('<br>\n')))

    return text


###################
# CONVERT TO TEXT #
###################

def is_html_element(element) -> bool:
    return element.name is not None


def is_link(element):
    if element.name != 'a':
        return False

    if len(list(filter(is_html_element, element.contents))) > 1:
        return False

    return True


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


def is_br(element):
    return element.name == 'br' and not element.get_text(' ')


def is_comment(element):
    return isinstance(element, Comment) or isinstance(element, ProcessingInstruction)


def get_element_and_text(element):
    return element.contents


def build_text(soup: BeautifulSoup) -> tuple[str, int]:
    if is_table(soup):
        return refine_table_or_calendar(soup), 0

    result_line = ''
    current_line = ''
    total_calendar_items = 0
    for element in get_element_and_text(soup):
        if is_span(element):
            cleaned_text = clean_text(element.get_text(' '))
            if not cleaned_text:
                continue

            current_line = current_line + (' ' if current_line else '') + cleaned_text
        elif is_text(element):
            cleaned_text = clean_text(str(element))
            if not cleaned_text:
                continue

            current_line = current_line + (' ' if current_line else '') + cleaned_text
        elif is_br(element):
            if current_line:
                result_line = result_line + ('<br>\n' if result_line else '') + current_line
                total_calendar_items += int(is_calendar_item(current_line))
                current_line = ''
        elif is_comment(element):
            continue
        elif is_link(element):
            clear_link_formatting(element)
            cleaned_text = flatten_string(element.prettify())
            if not cleaned_text:
                continue

            current_line = current_line + (' ' if current_line else '') + cleaned_text
        else:
            text, nb_calendar_items = build_text(element)
            if text:
                if current_line:
                    result_line = result_line + ('<br>\n' if result_line else '') + current_line
                    total_calendar_items += int(is_calendar_item(current_line))
                    current_line = ''
                result_line = result_line + ('<br>\n' if result_line else '') + text
                total_calendar_items += nb_calendar_items

    if current_line:
        result_line = result_line + ('<br>\n' if result_line else '') + current_line
        total_calendar_items += int(is_calendar_item(current_line))

    if total_calendar_items > 1:
        return refine_table_or_calendar(soup), 0

    return result_line, total_calendar_items


###############
# REMOVE LINK #
###############

def remove_link_from_html(html: str) -> str:
    # https://stackoverflow.com/a/41496131
    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning, module='bs4')

    return clean_text(BeautifulSoup(html, 'html.parser').text)


def get_text_if_not_table(html: str) -> Optional[str]:
    element = BeautifulSoup(html, 'html.parser')
    if is_table(element):
        return None

    return element.text


########
# MAIN #
########

def refine_confession_content(content_html: str) -> str | None:
    if content_html is None:
        return None

    try:
        soup = BeautifulSoup(content_html, 'html.parser')
    except Exception as e:
        print(e)
        return None

    # This is hack to handle broken html
    pretty_content = soup.prettify()
    # Remove multiple consecutive spaces
    pretty_content = re.sub(r'\n\s*', ' ', pretty_content)
    soup = BeautifulSoup(pretty_content, 'html.parser')

    soup = remove_img(soup)
    soup = remove_script(soup)

    text, _ = build_text(soup)

    text = clean_paragraph(text)

    return text
