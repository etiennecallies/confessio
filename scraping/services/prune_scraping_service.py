from datetime import timedelta
from typing import Optional
from uuid import UUID

from background_task import background
from background_task.tasks import TaskSchedule
from django.db import IntegrityError, transaction
from django.utils import timezone
from tqdm import tqdm

from home.models import Pruning, PruningModeration, Page
from home.models import Sentence
from home.utils.log_utils import info
from scraping.extract.extract_content import BaseActionInterface
from scraping.extract.extract_content import extract_paragraphs_lines_and_indices
from scraping.extract.extract_interface import ExtractMode
from scraping.extract_v2.extract_content import extract_paragraphs_lines_and_indices_v2
from scraping.extract_v2.models import EventMotion, Temporal
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
    def __init__(self, pruning: Pruning | None = None):
        self.pruning = pruning

    def get_tags_and_event_motion(self, stringified_line: str
                                  ) -> tuple[set[Temporal], EventMotion, bool, UUID | None]:
        sentence = self.get_sentence(stringified_line)
        if self.pruning:
            sentence.prunings.add(self.pruning)

        temporal_tags = set()
        if sentence.human_temporal is not None or sentence.ml_temporal is not None:
            temporal = Temporal(sentence.human_temporal or sentence.ml_temporal)
            if temporal == Temporal.SCHED:
                temporal_tags.add(Temporal.SCHED)
            elif temporal == Temporal.SPEC:
                temporal_tags.add(Temporal.SPEC)
        else:
            raise ValueError(f'Sentence {sentence.uuid} has no human '
                             f'temporal nor ML temporal')

        if sentence.human_confession_legacy is not None:
            event_motion = EventMotion(sentence.human_confession_legacy)
        elif sentence.ml_confession_legacy is not None:
            event_motion = EventMotion(sentence.ml_confession_legacy)
        else:
            raise ValueError(f'Sentence {sentence.uuid} has no human '
                             f'confession nor ML confession')

        return temporal_tags, event_motion, False, sentence.uuid

    def get_sentence(self, stringified_line: str) -> Sentence:
        try:
            return Sentence.objects.get(line=stringified_line)
        except Sentence.DoesNotExist:
            if not self.pruning:
                raise ValueError(f'Sentence does not exist for line {stringified_line}')
            return classify_and_create_sentence(stringified_line, self.pruning)


class MLSentenceQualifyLineInterface(SentenceQualifyLineInterface):
    def get_tags_and_event_motion(self, stringified_line: str
                                  ) -> tuple[set[Temporal], EventMotion, bool, UUID | None]:
        sentence = self.get_sentence(stringified_line)
        if self.pruning:
            sentence.prunings.add(self.pruning)

        temporal_tags = set()
        if sentence.ml_temporal is not None:
            temporal = Temporal(sentence.ml_temporal)
            if temporal == Temporal.SCHED:
                temporal_tags.add(Temporal.SCHED)
            elif temporal == Temporal.SPEC:
                temporal_tags.add(Temporal.SPEC)
        else:
            raise ValueError(f'Sentence {sentence.uuid} has no ML temporal')

        if sentence.ml_confession_legacy is not None:
            event_motion = EventMotion(sentence.ml_confession_legacy)
        else:
            raise ValueError(f'Sentence {sentence.uuid} has no ML confession')

        return temporal_tags, event_motion, False, sentence.uuid


##############################
# REPRUNE AFFECTED SCRAPINGS #
##############################

def reprune_affected_prunings(sentences: list[Sentence], original_pruning: Pruning):
    worker_reprune_affected_prunings([str(s.uuid) for s in sentences], str(original_pruning.uuid))


@background(queue='main', schedule=TaskSchedule(priority=4))
def worker_reprune_affected_prunings(sentence_uuids: list[str], original_pruning_uuid: str):
    try:
        original_pruning = Pruning.objects.get(uuid=UUID(original_pruning_uuid))
    except Pruning.DoesNotExist:
        print(f'Pruning with uuid {original_pruning_uuid} does not exist, skipping repruning')
        return

    sentences = Sentence.objects.filter(uuid__in=sentence_uuids).all()
    if not sentences:
        print(f'No sentences found for uuids {sentence_uuids}, skipping repruning')
        return

    affected_prunings = []
    for sentence in sentences:
        for pruning in sentence.prunings.all():
            if pruning.uuid == original_pruning.uuid:
                continue

            if pruning not in affected_prunings:
                affected_prunings.append(pruning)

    print(f'got {len(affected_prunings)} affected prunings')
    for pruning in tqdm(affected_prunings):
        if remove_pruning_moderation_if_orphan(pruning):
            # pruning has been deleted, we do not need to reprune it
            continue

        print(f'repruning affected pruning {pruning}')
        prune_pruning(pruning)


def remove_pruning_moderation_if_orphan(pruning: Optional[Pruning]):
    """
    :return: True if the pruning has been deleted
    """
    if not pruning:
        return True

    if not pruning.scrapings.exists() and not pruning.images.exists():
        info(f'deleting not validated moderation for pruning {pruning} since it has no scraping '
             f'nor image any more')
        PruningModeration.objects.filter(pruning=pruning, validated_at__isnull=True).delete()
        return True

    return False


##############
# MODERATION #
##############

def get_current_moderation(pruning: Pruning,
                           category: PruningModeration.Category) -> Optional[PruningModeration]:
    try:
        return PruningModeration.objects.get(pruning=pruning, category=category)
    except PruningModeration.DoesNotExist:
        return None


def delete_moderation(pruning: Pruning, category: PruningModeration.Category) -> None:
    PruningModeration.objects.filter(pruning=pruning, category=category).delete()


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

    if get_current_moderation(pruning, category) is not None:
        # moderation already exists, we do not need to create a new one
        return

    moderation = PruningModeration(
        pruning=pruning,
        category=category,
        diocese=pruning.get_diocese(),
    )
    try:
        with transaction.atomic():
            moderation.save()
    except IntegrityError:
        info(f'PruningModeration for pruning {pruning} and category {category} '
             f'already exists, skipping creation')


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


def add_necessary_moderation_v2(pruning: Pruning):
    if pruning.v2_indices == pruning.human_indices \
            or (pruning.human_indices is None and pruning.v2_indices == pruning.ml_indices):
        delete_moderation(pruning, PruningModeration.Category.V2_DIFF_HUMAN)
        delete_moderation(pruning, PruningModeration.Category.V2_DIFF_V1)
        return

    if pruning.human_indices is not None and pruning.v2_indices != pruning.human_indices:
        add_new_moderation(pruning, PruningModeration.Category.V2_DIFF_HUMAN)
        delete_moderation(pruning, PruningModeration.Category.V2_DIFF_V1)
        return

    delete_moderation(pruning, PruningModeration.Category.V2_DIFF_HUMAN)
    add_new_moderation(pruning, PruningModeration.Category.V2_DIFF_V1)


####################
# LINK TO PARSINGS #
####################

def update_parsings(pruning: Pruning):
    websites = set()

    # Add scrapings' websites
    for scraping in pruning.scrapings.select_related("page").select_related("page__website").all():
        try:
            websites.add(scraping.page.website)
        except Page.DoesNotExist:
            print(f'Warning: scraping {scraping} has no page, skipping it for parsing')
            # TODO delete this scraping?

    # Add images' websites
    for image in pruning.images.select_related("website").all():
        websites.add(image.website)

    for website in websites:
        parse_pruning_for_website(pruning, website)


########
# MAIN #
########


def prune_pruning(pruning: Pruning) -> ():
    assert pruning.extracted_html, 'Pruning must have not empty extracted_html'

    # V1
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

    # V2
    paragraphs_v2 = extract_paragraphs_lines_and_indices_v2(pruning.extracted_html,
                                                            SentenceQualifyLineInterface(pruning),
                                                            ExtractMode.PRUNE)
    v2_indices = sum([indices for _, indices in paragraphs_v2], [])
    if v2_indices != pruning.v2_indices:
        pruning.v2_indices = v2_indices
        pruning.save()

        add_necessary_moderation_v2(pruning)

    update_parsings(pruning)


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
