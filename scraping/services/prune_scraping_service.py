import asyncio
from datetime import timedelta
from typing import Optional
from uuid import UUID

from django.utils import timezone
from tqdm import tqdm

from home.models import Pruning, PruningModeration, Website
from home.models import Sentence
from scraping.extract.extract_content import BaseActionInterface, ExtractMode
from scraping.extract.extract_content import extract_paragraphs_lines_and_indices
from scraping.prune.models import Action, Source
from scraping.services.classify_sentence_service import classify_and_create_sentence
from scraping.services.parse_pruning_service import parse_pruning_for_website


###################
# TAGGING WITH DB #
###################

class SentenceFromDbActionInterface(BaseActionInterface):
    def __init__(self, pruning: Pruning):
        self.pruning = pruning

    def get_action(self, line_without_link: str) -> tuple[Action, Source, UUID]:
        sentence = self.get_sentence(line_without_link)
        sentence.prunings.add(self.pruning)

        return Action(sentence.action), Source(sentence.source), sentence.uuid

    def get_sentence(self, line_without_link: str) -> Sentence:
        try:
            return Sentence.objects.get(line=line_without_link)
        except Sentence.DoesNotExist:
            return classify_and_create_sentence(line_without_link, self.pruning)


##############################
# REPRUNE AFFECTED SCRAPINGS #
##############################

def reprune_affected_prunings(sentences: list[Sentence], original_pruning: Pruning):
    affected_prunings = []
    for sentence in sentences:
        for pruning in sentence.prunings.all():
            if pruning.uuid == original_pruning.uuid:
                continue

            if pruning not in affected_prunings:
                affected_prunings.append(pruning)

    print(f'got {len(affected_prunings)} affected prunings')
    for pruning in tqdm(affected_prunings):
        if remove_pruning_if_orphan(pruning):
            # pruning has been deleted, we do not need to reprune it
            continue

        print(f'repruning affected pruning {pruning}')
        prune_pruning(pruning)


def remove_pruning_if_orphan(pruning: Optional[Pruning]):
    """
    :return: True if the pruning has been deleted
    """
    if not pruning:
        return True

    if not pruning.scrapings.exists():
        print(f'deleting not validated moderation for pruning {pruning} since it has no scraping '
              f'any more')
        PruningModeration.objects.filter(pruning=pruning, validated_at__isnull=True).delete()
        return True

    return False


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
        diocese=pruning.get_diocese(),
    )
    moderation.save()


def add_necessary_moderation(pruning: Pruning):
    if not is_eligible_to_pruning_moderation(pruning):
        return

    category = PruningModeration.Category.NEW_PRUNED_HTML
    current_moderation = get_current_moderation(pruning, category)

    if pruning.ml_indices == pruning.human_indices:
        if current_moderation is not None:
            current_moderation.delete()
        return

    # 1. If pruning has already moderation
    if current_moderation is not None:
        if current_moderation.validated_at is None:
            # moderation is not validated yet, we just keep it
            return

        # moderation has been validated
        current_moderation.delete()

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

async def update_parsings(pruning: Pruning):
    websites = set()

    # Add scrapings' websites
    async for scraping in pruning.scrapings.select_related("page").select_related("page__website")\
            .all():
        websites.add(scraping.page.website)

    # Add images' websites
    async for image in pruning.images.select_related("website").all():
        websites.add(image.website)

    for website in websites:
        await parse_pruning_for_website(pruning, website)


########
# MAIN #
########


def prune_pruning(pruning: Pruning, no_parsing: bool = False) -> ():
    assert pruning.extracted_html, 'Pruning must have not empty extracted_html'

    paragraphs = extract_paragraphs_lines_and_indices(pruning.extracted_html,
                                                      SentenceFromDbActionInterface(pruning),
                                                      ExtractMode.PRUNE)
    ml_indices = sum([indices for _, indices in paragraphs], [])

    if ml_indices != pruning.ml_indices:
        pruning.ml_indices = ml_indices
        if pruning.human_indices is None:
            pruning.pruned_indices = ml_indices
        pruning.save()

        add_necessary_moderation(pruning)

    if not no_parsing:
        asyncio.run(update_parsings(pruning))


def create_pruning(extracted_html: Optional[str]) -> Optional[Pruning]:
    if not extracted_html:
        return None

    try:
        pruning = Pruning.objects.get(extracted_html=extracted_html)
    except Pruning.DoesNotExist:
        pruning = Pruning(
            extracted_html=extracted_html,
        )
        pruning.save()

    return pruning
