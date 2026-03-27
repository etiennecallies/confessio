from django.db.models.functions import Now

from crawling.models import CrawlingModeration
from registry.models import Website
from scheduling.models import Scheduling
from scheduling.models.scheduling_moderation_models import SchedulingModeration, \
    ValidatedSchedulesModeration
from scheduling.services.merging.schedules_conflict_service import website_has_schedules_conflict
from scheduling.services.scheduling.index_scheduling_service import SchedulingIndexingObjects
from scheduling.services.scheduling.scheduling_service import get_scheduling_sources


def upsert_scheduling_moderation(website: Website, category: SchedulingModeration.Category,
                                 moderation_validated: bool):
    try:
        moderation = SchedulingModeration.objects.get(website=website)
        if moderation.category != category:
            moderation.category = category
            moderation.validated_at = Now() if moderation_validated else None
            moderation.validated_by = None
            moderation.save()
    except SchedulingModeration.DoesNotExist:
        moderation = SchedulingModeration(
            website=website, category=category,
            diocese=website.get_diocese(),
            validated_at=Now() if moderation_validated else None,
        )
        moderation.save()


def has_crawling_moderation_been_validated(scheduling: Scheduling) -> bool:
    return CrawlingModeration.objects.filter(
        website=scheduling.website,
        category__in=[CrawlingModeration.Category.NO_RESPONSE, CrawlingModeration.Category.NO_PAGE],
        validated_at__isnull=False
    ).exists()


def get_scheduling_moderation_category(scheduling: Scheduling,
                                       indexing_objects: SchedulingIndexingObjects
                                       ) -> tuple[SchedulingModeration.Category, bool]:
    scheduling_sources = get_scheduling_sources(scheduling)
    if not scheduling_sources.parsings and not scheduling_sources.oclocher_schedules:
        moderation_validated = has_crawling_moderation_been_validated(scheduling)
        return SchedulingModeration.Category.NO_SOURCE, moderation_validated

    if not indexing_objects.index_events:
        return SchedulingModeration.Category.NO_SCHEDULE, False

    if not all(map(lambda s: s.is_real_church(),
                   indexing_objects.sourced_schedules_list.sourced_schedules_of_churches)):
        return SchedulingModeration.Category.UNKNOWN_PLACE, False

    if website_has_schedules_conflict(indexing_objects.index_events):
        return SchedulingModeration.Category.SCHEDULES_CONFLICT, False

    return SchedulingModeration.Category.OK, True


def handle_scheduling_moderation(scheduling: Scheduling,
                                 indexing_objects: SchedulingIndexingObjects):
    category, moderation_validated = get_scheduling_moderation_category(scheduling,
                                                                        indexing_objects)
    upsert_scheduling_moderation(scheduling.website, category, moderation_validated)


def upsert_website_schedules_moderation(website: Website,
                                        category: ValidatedSchedulesModeration.Category,
                                        moderation_validated: bool):
    try:
        moderation = ValidatedSchedulesModeration.objects.get(website=website)
        if moderation.category != category:
            moderation.category = category
            moderation.validated_at = Now() if moderation_validated else None
            moderation.validated_by = None
            moderation.save()
    except ValidatedSchedulesModeration.DoesNotExist:
        moderation = ValidatedSchedulesModeration(
            website=website, category=category,
            diocese=website.get_diocese(),
            validated_at=Now() if moderation_validated else None,
        )
        moderation.save()


def get_website_schedules_moderation_category(
        indexing_objects: SchedulingIndexingObjects
) -> tuple[ValidatedSchedulesModeration.Category, bool] | None:
    if indexing_objects.schedules_match_with_validated is None:
        return None

    if not indexing_objects.schedules_match_with_validated:
        return ValidatedSchedulesModeration.Category.SCHEDULES_DIFFERS, False

    return ValidatedSchedulesModeration.Category.OK, True


def handle_website_schedules_moderation(scheduling: Scheduling,
                                        indexing_objects: SchedulingIndexingObjects):
    category_and_validation = get_website_schedules_moderation_category(indexing_objects)
    if category_and_validation is None:
        return
    category, moderation_validated = category_and_validation
    upsert_website_schedules_moderation(scheduling.website, category, moderation_validated)


def add_necessary_scheduling_moderation(scheduling: Scheduling,
                                        indexing_objects: SchedulingIndexingObjects):
    handle_scheduling_moderation(scheduling, indexing_objects)
    handle_website_schedules_moderation(scheduling, indexing_objects)
