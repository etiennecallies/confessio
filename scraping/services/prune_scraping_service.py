from typing import Optional

from django.db.models import Q

from home.models import Scraping, Pruning, PruningModeration
from home.models import Sentence
from scraping.extract.extract_content import BaseTagInterface
from scraping.extract.extract_content import extract_content
from scraping.prune.models import Action, Source
from scraping.services.classify_sentence_service import classify_sentence
from scraping.services.sentence_action_service import get_sentence_action, get_sentence_source


###################
# TAGGING WITH DB #
###################

class SentenceFromDbTagInterface(BaseTagInterface):
    def __init__(self, pruning: Pruning):
        self.pruning = pruning

    def get_action(self, line_without_link: str) -> tuple[Action, Optional[Source]]:
        try:
            sentence = Sentence.objects.get(line=line_without_link)
        except Sentence.DoesNotExist:
            sentence = classify_sentence(line_without_link, self.pruning)

        return get_sentence_action(sentence), get_sentence_source(sentence)


##############################
# REPRUNE AFFECTED SCRAPINGS #
##############################

def reprune_affected_scrapings(sentences: list[Sentence], original_pruning: Pruning):
    query = Q()
    for sentence in sentences:
        query |= Q(extracted_html__contains=sentence.line)
    affected_prunings = Pruning.objects.filter(query)\
        .exclude(uuid=original_pruning.uuid).all()
    for pruning in affected_prunings:
        # delete pruning if it has no scraping
        if not pruning.scrapings.exists():
            print(f'deleting pruning {pruning} since it has no scraping any more')
            pruning.delete()
            continue

        print(f'repruning affected pruning {pruning}')
        prune_pruning(pruning)


##############
# MODERATION #
##############

def get_current_moderation(pruning: Pruning,
                           category) -> Optional[PruningModeration]:
    try:
        return PruningModeration.objects.get(pruning=pruning, category=category)
    except PruningModeration.DoesNotExist:
        return None


def add_new_moderation(pruning: Pruning, category):
    moderation = PruningModeration(
        pruning=pruning,
        category=category,
        pruned_html=pruning.pruned_html,
        pruned_indices=pruning.pruned_indices,
    )
    moderation.save()


def add_necessary_moderation(pruning: Pruning):
    category = PruningModeration.Category.NEW_PRUNED_HTML

    # 1. If pruning has already moderation
    current_moderation = get_current_moderation(pruning, category)
    if current_moderation is not None:
        if current_moderation.pruned_html == pruning.pruned_html\
                and current_moderation.pruned_indices == pruning.pruned_indices:
            # pruned_html has not changed, we do nothing
            return

        if current_moderation.validated_at is None:
            # confession_html_pruned has changed, but not validated yet, we just update it
            current_moderation.pruned_html = pruning.pruned_html
            current_moderation.pruned_indices = pruning.pruned_indices
            current_moderation.save()
            return

        # confession_html_pruned has changed and was validated, we remove it and add a new one
        current_moderation.delete()
        add_new_moderation(pruning, category)
        return

    # 2. No moderation for this scraping yet. We add new moderation, only if not already exists
    add_new_moderation(pruning, category)


########
# MAIN #
########

def prune_pruning(pruning: Pruning) -> ():
    assert pruning.extracted_html, 'Pruning must have not empty extracted_html'

    paragraphs, indices = extract_content(pruning.extracted_html,
                                          SentenceFromDbTagInterface(pruning))
    pruned_html = '<br>\n'.join(paragraphs) if paragraphs else None

    if pruned_html == pruning.pruned_html and indices == pruning.pruned_indices:
        return

    pruning.pruned_html = pruned_html
    pruning.pruned_indices = indices
    pruning.save()

    add_necessary_moderation(pruning)


def prune_scraping_and_save(scraping: Scraping):
    extracted_html = scraping.confession_html
    if not extracted_html:
        return

    try:
        pruning = Pruning.objects.get(extracted_html=extracted_html)
    except Pruning.DoesNotExist:
        pruning = Pruning(
            extracted_html=extracted_html,
        )
        pruning.save()

    prune_pruning(pruning)
    scraping.pruning = pruning
    scraping.save()
