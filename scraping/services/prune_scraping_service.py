from typing import List

from django.db.models import Q
from django.db.models.functions import Now

from home.models import Scraping, ScrapingModeration
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


##############
# MODERATION #
##############

def add_necessary_moderation(scraping: Scraping):
    if scraping.confession_html_pruned is None:
        # TODO we might want to moderate when scraping has been nullified by pruning
        return

    category = ScrapingModeration.Category.CONFESSION_HTML_PRUNED_NEW

    # First we delete every previous unvalidated moderation or current moderation
    moderations_to_delete = ScrapingModeration.objects\
        .filter(scraping__page__exact=scraping.page,
                category=category)\
        .filter(Q(scraping__exact=scraping) | Q(validated_at__isnull=True))

    for moderation_to_delete in moderations_to_delete:
        if moderation_to_delete.scraping == scraping and moderation_to_delete.validated_at is None:
            moderation_to_delete.confession_html_pruned = scraping.confession_html_pruned
            moderation_to_delete.save()
        else:
            moderation_to_delete.delete()

    try:
        ScrapingModeration.objects.get(confession_html_pruned=scraping.confession_html_pruned)
    except ScrapingModeration.DoesNotExist:
        moderation = ScrapingModeration(
            scraping=scraping,
            category=category,
            confession_html_pruned=scraping.confession_html_pruned,
        )
        moderation.save()


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

    add_necessary_moderation(scraping)
