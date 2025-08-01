import asyncio
from datetime import timedelta
from typing import Optional
from uuid import UUID

from django.utils import timezone
from tqdm import tqdm

from home.models import Pruning, PruningModeration, Page
from home.models import Sentence
from scraping.extract.extract_content import BaseActionInterface
from scraping.extract.extract_content import extract_paragraphs_lines_and_indices
from scraping.extract.extract_interface import ExtractMode
from scraping.extract_v2.models import TagV2, EventMotion
from scraping.extract_v2.qualify_line_interfaces import BaseQualifyLineInterface
from scraping.prune.models import Action, Source
from scraping.services.classify_sentence_service import classify_and_create_sentence
from scraping.services.parse_pruning_service import parse_pruning_for_website


######################
# TAGGING WITH DB V1 #
######################

class SentenceFromDbActionInterface(BaseActionInterface):
    def __init__(self, pruning: Pruning):
        self.pruning = pruning

    def get_action(self, stringified_line: str) -> tuple[Action, Source, UUID]:
        sentence = self.get_sentence(stringified_line)
        sentence.prunings.add(self.pruning)

        return Action(sentence.action), Source(sentence.source), sentence.uuid

    def get_sentence(self, stringified_line: str) -> Sentence:
        try:
            return Sentence.objects.get(line=stringified_line)
        except Sentence.DoesNotExist:
            return classify_and_create_sentence(stringified_line, self.pruning)


######################
# TAGGING WITH DB V2 #
######################

class SentenceQualifyLineInterface(BaseQualifyLineInterface):
    def __init__(self, pruning: Pruning):
        self.pruning = pruning

    def get_tags_and_event_motion(self, stringified_line: str) -> tuple[set[TagV2], EventMotion]:
        sentence = self.get_sentence(stringified_line)
        sentence.prunings.add(self.pruning)

        tags = set()
        if sentence.human_schedule is not None:
            if sentence.human_schedule:
                tags.add(TagV2.SCHEDULE)
        elif sentence.ml_schedule is not None:
            if sentence.ml_schedule:
                tags.add(TagV2.SCHEDULE)
        else:
            raise ValueError(f'Sentence {sentence.uuid} has no human schedule nor ML schedule')
        if sentence.human_specifier is not None:
            if sentence.human_specifier:
                tags.add(TagV2.SPECIFIER)
        elif sentence.ml_specifier is not None:
            if sentence.ml_specifier:
                tags.add(TagV2.SPECIFIER)
        else:
            raise ValueError(f'Sentence {sentence.uuid} has no human specifier nor ML specifier')

        if sentence.human_confession is not None:
            event_motion = EventMotion(sentence.human_confession)
        elif sentence.ml_confession is not None:
            event_motion = EventMotion(sentence.ml_confession)
        else:
            raise ValueError(f'Sentence {sentence.uuid} has no human '
                             f'confession nor ML confession')

        return tags, event_motion

    def get_sentence(self, stringified_line: str) -> Sentence:
        try:
            return Sentence.objects.get(line=stringified_line)
        except Sentence.DoesNotExist:
            return classify_and_create_sentence(stringified_line, self.pruning)


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

    if not pruning.scrapings.exists() and not pruning.images.exists():
        print(f'deleting not validated moderation for pruning {pruning} since it has no scraping '
              f'nor image any more')
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
# LINK TO PARSINGS #
####################

async def update_parsings(pruning: Pruning):
    websites = set()

    # Add scrapings' websites
    async for scraping in pruning.scrapings.select_related("page").select_related("page__website")\
            .all():
        try:
            websites.add(scraping.page.website)
        except Page.DoesNotExist:
            print(f'Warning: scraping {scraping} has no page, skipping it for parsing')
            # TODO delete this scraping?

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
