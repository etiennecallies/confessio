import re
import string

from unidecode import unidecode


def normalize_content(content):
    return unidecode(content.lower())


def get_words(content):
    for char in string.punctuation:
        content = content.replace(char, ' ')

    return set(content.split())


def has_any_of_words(content: str, lexical_list, regex_list=None, expr_list=None):
    normalized_content = normalize_content(content)
    words = get_words(normalized_content)

    for mention in lexical_list:
        if mention in words:
            return True

    if regex_list:
        for regex in regex_list:
            if re.findall(regex, normalized_content):
                return True

    if expr_list:
        for expr in expr_list:
            if expr in normalized_content:
                return True

    return False
