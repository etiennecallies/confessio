from django.contrib.auth.models import User

from home.models import Sentence, Scraping
from scraping.services.prune_scraping_service import SentenceFromDbTagInterface
from scraping.utils.extract_content import split_and_tag
from scraping.utils.prune_lines import get_pruned_lines_indices
from scraping.utils.tag_line import Tag, get_tags_with_regex


############################
# ADD ID AND COLOR TO TAGS #
############################

def get_colored_pieces(confession_html: str):
    lines_and_tags = split_and_tag(confession_html, SentenceFromDbTagInterface())
    kept_indices = get_pruned_lines_indices(lines_and_tags)

    tag_colors = {
        Tag.PERIOD: 'warning',
        Tag.DATE: 'black',
        Tag.SCHEDULE: 'purple',
        Tag.CONFESSION: 'success',
        Tag.PLACE: 'info',
        Tag.SPIRITUAL: 'danger',
        Tag.OTHER: 'gray',
    }

    colored_pieces = []
    for i, (text, text_without_link, tags) in enumerate(lines_and_tags):
        new_tags = {}
        for tag, color in tag_colors.items():
            new_tags[tag] = {
                'id': f'{i}-{tag}',
                'checked': tag in tags,
                'color': color
            }

        colored_pieces.append(
            {
                "text": text,
                "text_without_link": text_without_link,
                "color": '' if i in kept_indices else 'text-warning',
                "tags": new_tags
            }
        )

    return colored_pieces


#################
# SAVE SENTENCE #
#################

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


def save_sentence(line_without_link: str, scraping: Scraping, user: User,
                  checked_per_tag: dict[str, bool]):
    regex_tags = get_tags_with_regex(line_without_link)
    checked_tags = set([Tag(tag_name) for tag_name, checked in checked_per_tag.items() if checked])
    if regex_tags == checked_tags:
        # We don't save sentence if tags are equal with regex
        return

    try:
        sentence = Sentence.objects.get(line=line_without_link)
    except Sentence.DoesNotExist:
        sentence = Sentence(
            line=line_without_link,
            scraping=scraping,
            updated_by=user,
        )

    update_sentence(sentence, checked_per_tag)

    sentence.save()
