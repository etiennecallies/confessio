from typing import Optional

from django.db.models import Q
from django.db.models.functions import Now

from home.models import Scraping, ScrapingModeration
from home.models import Sentence
from scraping.extract.extract_content import BaseTagInterface
from scraping.extract.extract_content import extract_content
from scraping.prune.models import Action
from scraping.services.classify_sentence_service import classify_sentence
from scraping.services.sentence_action_service import get_sentence_action


###################
# TAGGING WITH DB #
###################

class SentenceFromDbTagInterface(BaseTagInterface):
    def __init__(self, scraping: Scraping):
        self.scraping = scraping

    def get_action(self, line_without_link: str) -> Action:
        try:
            sentence = Sentence.objects.get(line=line_without_link)
        except Sentence.DoesNotExist:
            sentence = classify_sentence(line_without_link, self.scraping)

        return get_sentence_action(sentence)


##############################
# REPRUNE AFFECTED SCRAPINGS #
##############################

def reprune_affected_scrapings(sentences: list[Sentence], original_scraping: Scraping):
    query = Q()
    for sentence in sentences:
        query |= Q(confession_html__contains=sentence.line)
    affected_scrapings = Scraping.objects.filter(query)\
        .exclude(uuid=original_scraping.uuid).all()
    for scraping in affected_scrapings:
        print(f'repruning affected scraping {scraping}')
        prune_scraping_and_save(scraping)


##############
# MODERATION #
##############

def get_current_moderation(scraping: Scraping,
                           category) -> Optional[ScrapingModeration]:
    try:
        return ScrapingModeration.objects.get(scraping=scraping, category=category)
    except ScrapingModeration.DoesNotExist:
        return None


def add_new_moderation(scraping: Scraping, category):
    moderation = ScrapingModeration(
        scraping=scraping,
        category=category,
        confession_html=scraping.confession_html,
        indices=scraping.indices,
    )
    moderation.save()


def similar_scraping_exists(confession_html, indices) -> bool:
    try:
        ScrapingModeration.objects.get(confession_html=confession_html, indices=indices)
        return True
    except ScrapingModeration.DoesNotExist:
        return False


def add_necessary_moderation(scraping: Scraping):
    category = ScrapingModeration.Category.CONFESSION_HTML_PRUNED_NEW

    # first, we delete every previous unvalidated moderation of this page
    moderations_to_delete = ScrapingModeration.objects\
        .filter(scraping__page__exact=scraping.page,
                category=category,
                validated_at__isnull=True)\
        .exclude(scraping=scraping)

    for moderation_to_delete in moderations_to_delete:
        moderation_to_delete.delete()

    # 1. If confession_html is empty. We just remove moderation if exists.
    if scraping.confession_html is None:
        try:
            moderation = ScrapingModeration.objects.get(scraping=scraping, category=category)
            moderation.delete()
        except ScrapingModeration.DoesNotExist:
            pass

        return

    # 2. If scraping has already moderation
    current_moderation = get_current_moderation(scraping, category)
    if current_moderation is not None:
        if current_moderation.confession_html == scraping.confession_html\
                and current_moderation.indices == scraping.indices:
            # confession_html_pruned has not changed, we do nothing
            return

        if similar_scraping_exists(scraping.confession_html, scraping.indices):
            # confession_html_pruned has changed, but a moderation already exists,
            # we only delete obsolete moderation.
            current_moderation.delete()
            return

        if current_moderation.validated_at is None:
            # confession_html_pruned has changed, but not validated yet, we just update it
            current_moderation.confession_html = scraping.confession_html
            current_moderation.indices = scraping.indices
            current_moderation.save()
            return

        # confession_html_pruned has changed and was validated, we remove it and add a new one
        current_moderation.delete()
        add_new_moderation(scraping, category)
        return

    # 3. No moderation for this scraping yet. We add new moderation, only if not already exists
    if not similar_scraping_exists(scraping.confession_html, scraping.indices):
        add_new_moderation(scraping, category)


########
# MAIN #
########

def prune_content(scraping: Scraping
                  ) -> tuple[Optional[str], Optional[list[int]]]:
    if not scraping.confession_html:
        return None, None

    paragraphs, indices = extract_content(scraping.confession_html,
                                          SentenceFromDbTagInterface(scraping))
    if not paragraphs:
        return None, indices

    return '<br>\n'.join(paragraphs), indices


def prune_scraping_and_save(scraping: Scraping):
    confession_html_pruned, indices = prune_content(scraping)
    if scraping.confession_html_pruned \
            and scraping.confession_html_pruned == confession_html_pruned\
            and scraping.indices == indices:
        return

    scraping.confession_html_pruned = confession_html_pruned
    scraping.indices = indices
    scraping.pruned_at = Now()
    scraping.save()

    add_necessary_moderation(scraping)
