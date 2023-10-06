from typing import List

from home.models import Sentence
from scraping.utils.refine_content import refine_confession_content, remove_link_from_html
from scraping.utils.string_search import has_any_of_words
from scraping.utils.tagging import tags_from_sentence, Tag

##################
# LEXICAL SEARCH #
##################

CONFESSIONS_MENTIONS = [
    'confession',
    'confessions',
    'confesse',
    'confesser',
    'reconciliation',
    'pardon',
]

SCHEDULES_MENTIONS = []

SCHEDULES_REGEX = [
    r'\dh',
    r'\d\dh',
    r'\dh\d\d',
    r'\d\dh\d\d',
    r'\d\d:\d\d',
    r'\d:\d\d',
]

SCHEDULES_EXPR = [
    'rendez-vous',
]

DATES_MENTIONS = [
    'jour',
    'jours',
    'matin',
    'matins',
    'soir',
    'soirs',
    'lundi',
    'lundis',
    'mardi',
    'mardis',
    'mercredi',
    'mercredis',
    'jeudi',
    'jeudis',
    'vendredi',
    'vendredis',
    'samedi',
    'samedis',
    'dimanche',
    'dimanches',
    'janvier',
    'fevrier',
    'mars',
    'avril',
    'mai',
    'juin',
    'juillet',
    'aout',
    'septembre',
    'octobre',
    'novembre',
    'decembre',
    'fete',
    'fetes',
]

DATES_EXPR = [
    'rendez-vous',
]

PERIOD_MENTIONS = [
    'careme',
    'temps',
    'ordinaire',
    'vacances',
    'scolaire',
    'scolaires',
]


def is_confession_mentions(content: str):
    return has_any_of_words(content, CONFESSIONS_MENTIONS)


def is_schedule_description(content: str):
    return has_any_of_words(content, SCHEDULES_MENTIONS, SCHEDULES_EXPR, SCHEDULES_REGEX)


def is_date_description(content: str):
    return has_any_of_words(content, DATES_MENTIONS, DATES_EXPR)


def is_period_description(content: str):
    return has_any_of_words(content, PERIOD_MENTIONS)


########
# TAGS #
########

def get_tags(line_without_link: str, use_sentence: bool) -> List[Tag]:
    sentence = None
    if use_sentence:
        try:
            sentence = Sentence.objects.get(line=line_without_link)
        except Sentence.DoesNotExist:
            sentence = None

    if sentence is None:
        sentence = Sentence(
            is_confession=is_confession_mentions(line_without_link),
            is_schedule=is_schedule_description(line_without_link),
            is_date=is_date_description(line_without_link),
            is_period=is_period_description(line_without_link),
            is_place=False,
            is_spiritual=False,
            is_other=False
        )

    return tags_from_sentence(sentence)


######################
# EXTRACT ON REFINED #
######################

MAX_BUFFERING_ATTEMPTS = 2


def get_confession_pieces(refined_content: str, use_sentence=False):
    results = []
    remaining_buffering_attempts = None
    buffer = []
    date_buffer = []

    # Split into lines (or <table>)
    for line in refined_content.split('<br>\n'):
        line_without_link = remove_link_from_html(line)

        tags = get_tags(line_without_link, use_sentence)
        line_and_tags = line, line_without_link, tags

        if Tag.SPIRITUAL in tags:
            # We ignore spiritual content
            continue

        if (Tag.SCHEDULE in tags or Tag.PERIOD in tags) \
                and (Tag.CONFESSION in tags or remaining_buffering_attempts is not None):
            # If we found schedules or period and were waiting for it

            # If we found schedules only, we add date_buffer
            if Tag.DATE not in tags:
                results.extend(date_buffer)

            results.extend(buffer)
            buffer = []
            results.append(line_and_tags)
            date_buffer = []
            remaining_buffering_attempts = MAX_BUFFERING_ATTEMPTS
        elif Tag.CONFESSION in tags \
                or (Tag.DATE in tags and remaining_buffering_attempts is not None):
            # If we found confessions, or date and waiting for it
            buffer.append(line_and_tags)
            remaining_buffering_attempts = MAX_BUFFERING_ATTEMPTS
        elif remaining_buffering_attempts == 0:
            # If we found nothing and we reached limit without anything
            buffer = []
            remaining_buffering_attempts = None
        elif remaining_buffering_attempts is not None:
            # If we found nothing, and we still have some remaining attempts left
            buffer.append(line_and_tags)
            remaining_buffering_attempts -= 1
        elif Tag.DATE in tags and Tag.SCHEDULE not in tags:
            # If we found date but not is_schedule we add line to date buffer
            date_buffer.append(line_and_tags)
        elif Tag.DATE in tags or Tag.SCHEDULE not in tags:
            # If we found both date and schedules OR neither of the two we clear date buffer
            date_buffer = []

    return results


def extract_content(refined_content: str, use_sentence=False):
    confession_pieces = get_confession_pieces(refined_content, use_sentence)
    if not confession_pieces:
        return []

    lines, _lines_without_link, _tags = zip(*confession_pieces)

    return lines


########
# MAIN #
########

def extract_confession_part_from_content(html_content):
    refined_content = refine_confession_content(html_content)
    if refined_content is None:
        return None

    paragraphs = extract_content(refined_content)
    if not paragraphs:
        return None

    return '<br>\n'.join(paragraphs)
