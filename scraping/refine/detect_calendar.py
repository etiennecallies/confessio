import re

from scraping.utils.html_utils import split_lines
from scraping.utils.string_search import normalize_content

DATES_REGEX = [
    r'(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])',
    r'\d\d\/\d\d/\d\d\d\d',
    r'\d\d jan',
    r'\d\d fev',
    r'\d\d mar',
    r'\d\d avr',
    r'\d\d mai',
    r'\d\d jui',
    r'\d\d aou',
    r'\d\d sep',
    r'\d\d oct',
    r'\d\d nov',
    r'\d\d dec',
    r'jan \d\d',
    r'fev \d\d',
    r'mar \d\d',
    r'avr \d\d',
    r'mai \d\d',
    r'jui \d\d',
    r'aou \d\d',
    r'sep \d\d',
    r'oct \d\d',
    r'nov \d\d',
    r'dec \d\d',
]


def trim_string(s: str) -> str:
    return s.strip()


def is_calendar_item(line: str) -> bool:
    normalized_line = normalize_content(trim_string(line))
    for regex in DATES_REGEX:
        if re.fullmatch(regex, normalized_line):
            return True

    return False


def is_calendar(cleaned_text: str) -> bool:
    lines = split_lines(cleaned_text)
    if sum(map(int, map(is_calendar_item, lines))) > 1:
        return True

    return False
