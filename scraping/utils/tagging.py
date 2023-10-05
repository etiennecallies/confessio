from enum import Enum
from typing import List

from home.models import Sentence


class Tag(Enum):
    CONFESSION = 'confession'
    SCHEDULE = 'schedule'
    DATE = 'date'
    PERIOD = 'period'
    PLACE = 'place'
    SPIRITUAL = 'spiritual'
    OTHER = 'other'


def tags_from_sentence(sentence: Sentence) -> List[Tag]:
    tags = []
    if sentence.is_confession:
        tags.append(Tag.CONFESSION)

    if sentence.is_schedule:
        tags.append(Tag.SCHEDULE)

    if sentence.is_date:
        tags.append(Tag.DATE)

    if sentence.is_period:
        tags.append(Tag.PERIOD)

    if sentence.is_place:
        tags.append(Tag.PLACE)

    if sentence.is_spiritual:
        tags.append(Tag.SPIRITUAL)

    if sentence.is_other:
        tags.append(Tag.OTHER)

    return tags


def update_sentence(sentence: Sentence, checked_per_tag):
    for tag_name, checked in checked_per_tag.items():
        if tag_name == Tag.PERIOD:
            sentence.is_period = checked
        if tag_name == Tag.DATE:
            sentence.is_date = checked
        if tag_name == Tag.SCHEDULE:
            sentence.is_schedule = checked
        if tag_name == Tag.CONFESSION:
            sentence.is_confession = checked
        if tag_name == Tag.PLACE:
            sentence.is_place = checked
        if tag_name == Tag.SPIRITUAL:
            sentence.is_spiritual = checked
        if tag_name == Tag.OTHER:
            sentence.is_other = checked
