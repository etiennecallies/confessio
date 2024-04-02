import re
import string

from unidecode import unidecode


def normalize_content(content):
    return unidecode(content.lower())


def unhyphen_content(content):
    return content.replace('-', ' ')


def get_words(content, punctuation=None):
    for char in (punctuation or string.punctuation):
        content = content.replace(char, ' ')

    return content.split()


def get_punctuation_except(regex_list):
    result = ''
    for char in string.punctuation:
        if not any([char in r for r in regex_list]):
            result += char

    return result


def get_consecutive_words(words, k):
    return [" ".join([words[i + j] for j in range(k)]) for i in range(len(words) + 1 - k)]


def has_any_of_words(content: str, lexical_list, expr_list=None, regex_list=None):
    normalized_content = normalize_content(content)

    if lexical_list:
        words_set = set(get_words(normalized_content))
        for mention in lexical_list:
            if mention in words_set:
                return True

    if expr_list:
        for expr in expr_list:
            if expr in normalized_content:
                return True

    if regex_list:
        punctuation = get_punctuation_except(regex_list)
        words = get_words(normalized_content, punctuation)
        for regex in regex_list:
            k = len(regex.split())  # number of words in regex
            for w in get_consecutive_words(words, k):
                if re.fullmatch(regex, w):
                    return True

    return False
