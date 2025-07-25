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
    'confessera',
    'reconciliation',
    'pardon',
    'absolution',
]

SCHEDULES_MENTIONS = [
    'heure',
    'heures',
    'apres',
    'avant',
    'pendant',
    'rdv',
    'rv',
    'supprime',
    'supprimes',
    'supprimee',
    'supprimees',
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
    r'\d\d: \d\d',
    r'\dh:',
    r'\d\dh:',
]

SCHEDULES_EXPR = [
    'rendez-vous',
    "a l'issue",
    'sur demande',
    'etre demande',
    "s'adresser",
    "vous adresser",
    "a la disposition",
    'lors de ',
    'lors des ',
    'aux horaires ',
    'au cours d',
    'au cours de',
    'autour des',
    'a tout moment',
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
    'lun',
    'mardi',
    'mardis',
    'mar',
    'mercredi',
    'mercredis',
    'mer',
    'jeudi',
    'jeudis',
    'jeu',
    'vendredi',
    'vendredis',
    'ven',
    'samedi',
    'samedis',
    'sam',
    'dimanche',
    'dimanches',
    'dim',
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
    r'(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])',
    r'\d\d\/\d\d/\d\d\d\d',
    r'\d\d\d\d\/\d\d\d\d',
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
]

PERIOD_MENTIONS = [
    'careme',
    'temps',
    'ordinaire',
    'vacances',
    'scolaire',
    'scolaires',
    'ete',
    'noel',
    'toussaint',
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

def get_tags_with_regex(stringified_line: str) -> Set[Tag]:
    tags = set()
    if is_confession_mentions(stringified_line):
        tags.add(Tag.CONFESSION)

    if is_schedule_description(stringified_line):
        tags.add(Tag.SCHEDULE)

    if is_date_description(stringified_line):
        tags.add(Tag.DATE)

    if is_period_description(stringified_line):
        tags.add(Tag.PERIOD)

    return tags
