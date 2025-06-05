import re

from scraping.utils.html_utils import split_lines
from scraping.utils.string_search import normalize_content

DATES_REGEX = [
    r'(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])',
    r'\d\d\/\d\d/\d\d\d\d',
    r'\d\d (jan|fev|mar|avr|mai|jui|aou|sep|oct|nov|dec)',
    r'(jan|fev|mar|avr|mai|jui|aou|sep|oct|nov|dec) \d\d',
    r"(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche) "
    r"(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) "
    r"([1-9]|[12][0-9]|3[01])",
    r"([1-9]|[12][0-9]|3[01])",
    r"(lun|mar|mer|jeu|ven|sam|dim)",
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
