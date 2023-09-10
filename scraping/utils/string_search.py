import re
import string

from unidecode import unidecode


def normalize_content(content):
    return unidecode(content.lower())


def get_words(content, punctuation=None):
    for char in (punctuation or string.punctuation):
        content = content.replace(char, ' ')

    return set(content.split())


def get_punctuation_except(regex_list):
    result = ''
    for char in string.punctuation:
        if not any([char in r for r in regex_list]):
            result += char

    return result


def has_any_of_words(content: str, lexical_list, expr_list=None, regex_list=None):
    normalized_content = normalize_content(content)

    if lexical_list:
        words = get_words(normalized_content)
        for mention in lexical_list:
            if mention in words:
                return True

    if expr_list:
        for expr in expr_list:
            if expr in normalized_content:
                return True

    if regex_list:
        punctuation = get_punctuation_except(regex_list)
        words = get_words(normalized_content, punctuation)
        for regex in regex_list:
            for w in words:
                if re.fullmatch(regex, w):
                    return True

    return False
