from enum import Enum
from typing import Set

from scraping.utils.string_search import has_any_of_words

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

SCHEDULES_MENTIONS = [
    'heure',
    'heures',
    'apres',
    'avant',
]

SCHEDULES_REGEX = [
    r'\dh',
    r'\d h',
    r'\d\dh',
    r'\d\d h',
    r'\dh\d\d',
    r'\d h \d\d',
    r'\d\dh\d\d',
    r'\d\d h \d\d',
    r'\d:\d\d',
    r'\d\d:\d\d',
    r'\dh:',
    r'\d\dh:',
]

SCHEDULES_EXPR = [
    'rendez-vous',
]

DATES_MENTIONS = [
    'date',
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

DATES_REGEX = [
    r'\d\d\/\d\d',
    r'\d\d\/\d\d/\d\d\d\d',
    r'\d\d\d\d\/\d\d\d\d',
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
    return has_any_of_words(content, DATES_MENTIONS, DATES_EXPR, DATES_REGEX)


def is_period_description(content: str):
    return has_any_of_words(content, PERIOD_MENTIONS)


########
# ENUM #
########

class Tag(str, Enum):
    CONFESSION = 'confession'
    SCHEDULE = 'schedule'
    DATE = 'date'
    PERIOD = 'period'


########
# MAIN #
########

def get_tags_with_regex(line_without_link: str) -> Set[Tag]:
    tags = set()
    if is_confession_mentions(line_without_link):
        tags.add(Tag.CONFESSION)

    if is_schedule_description(line_without_link):
        tags.add(Tag.SCHEDULE)

    if is_date_description(line_without_link):
        tags.add(Tag.DATE)

    if is_period_description(line_without_link):
        tags.add(Tag.PERIOD)

    return tags