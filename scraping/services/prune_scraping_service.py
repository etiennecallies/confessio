from typing import List

from django.db.models.functions import Now

from home.models import Scraping
from home.models import Sentence
from scraping.utils.extract_content import BaseTagInterface
from scraping.utils.extract_content import extract_content
from scraping.utils.tag_line import Tag, get_tags_with_regex


###################
# TAGGING WITH DB #
###################

class SentenceFromDbTagInterface(BaseTagInterface):
    def get_tags(self, line_without_link: str) -> List[Tag]:
        try:
            return tags_from_sentence(Sentence.objects.get(line=line_without_link))
        except Sentence.DoesNotExist:
            pass

        return get_tags_with_regex(line_without_link)


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


########
# MAIN #
########

def prune_content(refined_html):
    if not refined_html:
        return None

    paragraphs = extract_content(refined_html, SentenceFromDbTagInterface())
    if not paragraphs:
        return None

    return '<br>\n'.join(paragraphs)


def prune_scraping_and_save(scraping: Scraping):
    scraping.confession_html_pruned = prune_content(scraping.confession_html)
    scraping.pruned_at = Now()
    scraping.save()
