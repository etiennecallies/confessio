from scraping.utils.refine_content import refine_confession_content, remove_link_from_html
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


def has_confession_mentions(content: str):
    return has_any_of_words(content, CONFESSIONS_MENTIONS)


def is_schedule_description(content: str):
    return has_any_of_words(content, SCHEDULES_MENTIONS, SCHEDULES_EXPR, SCHEDULES_REGEX)


def is_date_description(content: str):
    return has_any_of_words(content, DATES_MENTIONS, DATES_EXPR)


def is_period_description(content: str):
    return has_any_of_words(content, PERIOD_MENTIONS)


######################
# EXTRACT ON REFINED #
######################

MAX_BUFFERING_ATTEMPTS = 2


def build_tags(has_confession, is_schedule, is_date, is_period, is_place, is_spiritual, is_other):
    tags = []
    if has_confession:
        tags.append('confession')

    if is_schedule:
        tags.append('schedule')

    if is_date:
        tags.append('date')

    if is_period:
        tags.append('period')

    if is_place:
        tags.append('place')

    if is_spiritual:
        tags.append('spiritual')

    if is_other:
        tags.append('other')

    return tags


def get_confession_pieces(refined_content: str):
    results = []
    remaining_buffering_attempts = None
    buffer = []
    date_buffer = []

    # Split into lines (or <table>)
    for line in refined_content.split('<br>\n'):
        line_without_link = remove_link_from_html(line)

        has_confession = has_confession_mentions(line_without_link)
        is_schedule = is_schedule_description(line_without_link)
        is_date = is_date_description(line_without_link)
        is_period = is_period_description(line_without_link)
        is_place = False
        is_spiritual = False
        is_other = False

        tags = build_tags(has_confession, is_schedule, is_date, is_period,
                          is_place, is_spiritual, is_other)
        line_and_tags = line, tags

        if (is_schedule or is_period) \
                and (has_confession or remaining_buffering_attempts is not None):
            # If we found schedules or period and were waiting for it

            # If we found schedules only, we add date_buffer
            if not is_date:
                results.extend(date_buffer)

            results.extend(buffer)
            buffer = []
            results.append(line_and_tags)
            date_buffer = []
            remaining_buffering_attempts = MAX_BUFFERING_ATTEMPTS
        elif has_confession or (is_date and remaining_buffering_attempts is not None):
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
        elif is_date and not is_schedule:
            # If we found date but not is_schedule we add line to date buffer
            date_buffer.append(line_and_tags)
        elif is_date or not is_schedule:
            # If we found both date and schedules OR neither of the two we clear date buffer
            date_buffer = []

    return results


def extract_content(refined_content: str):
    confession_pieces = get_confession_pieces(refined_content)
    if not confession_pieces:
        return []

    lines, tags = zip(*confession_pieces)

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
