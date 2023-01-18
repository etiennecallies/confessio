CONFESSIONS_MENTIONS = [
    'confession',
    'confessions',
    'reconciliation',
]


def get_paragraphs(content, page_type):
    # TODO split text into paragraphs (including title of paragraphs)
    return []


def normalize_content(content):
    # TODO remove html tags, accents, set it to lowercase
    return ''


def get_words(normalized_content):
    # TODO split words and punctuation
    return set()


def has_confession_mentions(content):
    normalized_content = normalize_content(content)
    words = get_words(normalized_content)

    for mention in CONFESSIONS_MENTIONS:
        if mention in words:
            return True

    return False


def extract_confession_part_from_content(content, page_type):
    paragraphs = get_paragraphs(content, page_type)
    delimiter = '<br>' if page_type == 'html' else '\n'

    return delimiter.join(filter(has_confession_mentions, paragraphs))
