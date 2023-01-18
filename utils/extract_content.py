import string
from unidecode import unidecode
import xml.etree.ElementTree as ET

CONFESSIONS_MENTIONS = [
    'confession',
    'confessions',
    'reconciliation',
]


def get_paragraphs(content, page_type):
    if page_type == 'html_page':
        myroot = ET.fromstring(content)
        # TODO continue

        return myroot

    # TODO split text into paragraphs (including title of paragraphs)
    return ['']


def normalize_content(content):
    return unidecode(content.lower())


def get_words(content):
    for char in string.punctuation:
        content = content.replace(char, ' ')

    return set(content.split())


def has_confession_mentions(content):
    normalized_content = normalize_content(content)
    words = get_words(normalized_content)

    for mention in CONFESSIONS_MENTIONS:
        if mention in words:
            return True

    return False


def extract_confession_part_from_content(content, page_type):
    paragraphs = get_paragraphs(content, page_type)
    delimiter = '<br>' if page_type == 'html_page' else '\n'

    return delimiter.join(filter(has_confession_mentions, paragraphs))
