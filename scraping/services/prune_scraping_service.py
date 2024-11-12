from datetime import timedelta
from typing import Optional

from django.db.models import Q
from django.utils import timezone

from home.models import Pruning, PruningModeration, ParsingModeration, Website
from home.models import Sentence
from scraping.extract.extract_content import BaseTagInterface
from scraping.extract.extract_content import extract_content
from scraping.prune.models import Action, Source
from scraping.services.classify_sentence_service import classify_sentence
from scraping.services.page_service import remove_pruning_if_orphan
from scraping.services.parse_pruning_service import parse_pruning_for_website


###################
# TAGGING WITH DB #
###################

class SentenceFromDbTagInterface(BaseTagInterface):
    def __init__(self, pruning: Pruning):
        self.pruning = pruning

    def get_action(self, line_without_link: str) -> tuple[Action, Source]:
        try:
            sentence = Sentence.objects.get(line=line_without_link)
        except Sentence.DoesNotExist:
            sentence = classify_sentence(line_without_link, self.pruning)

        return Action(sentence.action), Source(sentence.source)


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
        if remove_pruning_if_orphan(pruning):
            # pruning has been deleted, we do not need to reprune it
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


def pruning_needs_moderation(pruning: Pruning):
    for scraping in pruning.scrapings.all():
        page = scraping.page

        # If website has been marked as unreliable, we don't want to moderate it
        if page.website.unreliability_reason:
            break

        # if page has been validated less than three times or more than one year ago
        # and if website has been validated less than seven times or more than one year ago
        if (
                page.pruning_validation_counter < 3
                or page.pruning_last_validated_at is None
                or page.pruning_last_validated_at < (timezone.now() - timedelta(days=365))
        ) and (
                page.website.pruning_validation_counter < 7
                or page.website.pruning_last_validated_at is None
                or page.website.pruning_last_validated_at < (timezone.now() - timedelta(days=365))
        ):
            return True

    return False


def add_new_moderation(pruning: Pruning, category):
    if not pruning_needs_moderation(pruning):
        return

    moderation = PruningModeration(
        pruning=pruning,
        category=category,
        pruned_html=pruning.pruned_html,
        pruned_indices=pruning.pruned_indices,
    )
    moderation.save()


def add_necessary_moderation(pruning: Pruning):
    if not is_eligible_to_pruning_moderation(pruning):
        return

    category = PruningModeration.Category.NEW_PRUNED_HTML

    # 1. If pruning has already moderation
    current_moderation = get_current_moderation(pruning, category)
    if current_moderation is not None:
        if current_moderation.pruned_html == pruning.pruned_html\
                and current_moderation.pruned_indices == pruning.pruned_indices:
            # pruned_html has not changed, we do nothing
            return

        if current_moderation.validated_at is None:
            # pruned_html has changed, but not validated yet, we just update it
            current_moderation.pruned_html = pruning.pruned_html
            current_moderation.pruned_indices = pruning.pruned_indices
            current_moderation.save()
            return

        # pruned_html has changed and was validated, we remove it and add a new one
        current_moderation.delete()
        add_new_moderation(pruning, category)
        return

    # 2. No moderation for this scraping yet. We add new moderation, only if not already exists
    add_new_moderation(pruning, category)


####################
# MODERATION CLEAN #
####################

def is_eligible_to_pruning_moderation(pruning: Pruning):
    for scraping in pruning.scrapings.all():
        if scraping.page.website.unreliability_reason \
                != Website.UnreliabilityReason.SCHEDULE_IN_IMAGE:
            return True

    return False


def clean_pruning_moderations() -> int:
    counter = 0
    for pruning_moderation in PruningModeration.objects.filter(validated_at__isnull=True).all():
        if not is_eligible_to_pruning_moderation(pruning_moderation.pruning):
            pruning_moderation.delete()
            counter += 1

    return counter


####################
# LINK TO PARSINGS #
####################

def update_parsings(pruning: Pruning):
    for parsing in pruning.parsings.all():
        parsing.prunings.remove(pruning)

        if not parsing.prunings.exists():
            print(f'deleting not validated moderation for parsing {parsing} since it has no '
                  f'pruning any more')
            ParsingModeration.objects.filter(parsing=parsing,
                                             validated_at__isnull=True).delete()

    websites = {scraping.page.website for scraping in pruning.scrapings.all()}
    for website in websites:
        if website.unreliability_reason:
            continue

        # TODO open everywhere
        if website.parishes.filter(diocese__messesinfo_network_id__in=['lh', 'ly']).exists():
            print(f'parsing {pruning} for website {website}')
            parse_pruning_for_website(pruning, website)


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
    update_parsings(pruning)


def create_pruning(extracted_html: Optional[str]) -> Optional[Pruning]:
    if not extracted_html:
        return

    try:
        pruning = Pruning.objects.get(extracted_html=extracted_html)
    except Pruning.DoesNotExist:
        pruning = Pruning(
            extracted_html=extracted_html,
        )
        pruning.save()

    return pruning
