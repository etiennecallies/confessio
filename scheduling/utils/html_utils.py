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
