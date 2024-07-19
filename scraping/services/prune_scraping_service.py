from typing import Optional

from django.db.models.functions import Now

from home.models import Scraping, ScrapingModeration
from home.models import Sentence
from scraping.extract.extract_content import BaseTagInterface
from scraping.extract.extract_content import extract_content
from scraping.prune.models import Action
from scraping.services.classify_sentence_service import classify_sentence, get_sentence_action


###################
# TAGGING WITH DB #
###################

class SentenceFromDbTagInterface(BaseTagInterface):
    def __init__(self, scraping: Optional[Scraping]):
        self.scraping = scraping

    def get_action(self, line_without_link: str) -> Action:
        try:
            sentence = Sentence.objects.get(line=line_without_link)
        except Sentence.DoesNotExist:
            return Action.SHOW
            # TODO uncomment this line
            # sentence = classify_sentence(line_without_link, self.scraping)

        return get_sentence_action(sentence)


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
        confession_html_pruned=scraping.confession_html_pruned,
    )
    moderation.save()


def similar_scraping_exists(confession_html_pruned) -> bool:
    try:
        ScrapingModeration.objects.get(confession_html_pruned=confession_html_pruned)
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

    # 1. If confession_html_pruned is empty. We remove moderation if exists.
    if scraping.confession_html_pruned is None:
        try:
            moderation = ScrapingModeration.objects.get(scraping=scraping, category=category)
            moderation.delete()
        except ScrapingModeration.DoesNotExist:
            pass

        # TODO we might want to moderate when scraping has been nullified by pruning
        return

    # 2. If scraping has already moderation
    current_moderation = get_current_moderation(scraping, category)
    if current_moderation is not None:
        if current_moderation.confession_html_pruned == scraping.confession_html_pruned:
            # confession_html_pruned has not changed, we do nothing
            return

        if similar_scraping_exists(scraping.confession_html_pruned):
            # confession_html_pruned has changed, but a moderation already exists, we do nothing.
            return

        if current_moderation.validated_at is None:
            # confession_html_pruned has changed, but not validated yet, we just update it
            current_moderation.confession_html_pruned = scraping.confession_html_pruned
            current_moderation.save()
            return

        # confession_html_pruned has changed and was validated, we remove it and add a new one
        current_moderation.delete()
        add_new_moderation(scraping, category)
        return

    # 3. No moderation for this scraping yet. We add new moderation, only if not already exists
    if not similar_scraping_exists(scraping.confession_html_pruned):
        add_new_moderation(scraping, category)


########
# MAIN #
########

def prune_content(scraping: Scraping) -> Optional[str]:
    if not scraping.confession_html:
        return None

    paragraphs = extract_content(scraping.confession_html,
                                 SentenceFromDbTagInterface(scraping))
    if not paragraphs:
        return None

    return '<br>\n'.join(paragraphs)


def prune_scraping_and_save(scraping: Scraping):
    scraping.confession_html_pruned = prune_content(scraping)
    scraping.pruned_at = Now()
    scraping.save()

    add_necessary_moderation(scraping)
