import re
import warnings

from bs4 import MarkupResemblesLocatorWarning, BeautifulSoup


def split_lines(refined_content: str) -> list[str]:
    return refined_content.split('<br>\n')


def stringify_html(html: str) -> str:
    # https://stackoverflow.com/a/41496131
    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

    return remove_spaces(BeautifulSoup(html, 'html.parser').text)


def remove_spaces(text: str):
    text = re.sub(r'^\s*', '', text)
    text = re.sub(r'( )+', r' ', text)
    text = re.sub(r'\n ', r'\n', text)
    text = re.sub(r' \n', r'\n', text)
    text = re.sub(r'(\n)+', r'\n', text)
    text = re.sub(r'\s*$', '', text)
    text = text.strip()

    return text


def replace_link_by_their_content(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a'):
        if a.string:
            a.replace_with(a.string)
        else:
            a.decompose()  # Remove the link if it has no text
    return str(soup)
