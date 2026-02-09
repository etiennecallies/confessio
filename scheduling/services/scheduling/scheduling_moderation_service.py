from django.db.models.functions import Now

from crawling.models import CrawlingModeration
from registry.models import Website
from scheduling.models import Scheduling, IndexEvent
from scheduling.models.scheduling_moderation_models import SchedulingModeration
from scheduling.services.scheduling.schedules_conflict_service import website_has_schedules_conflict
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
                                       index_events: list[IndexEvent]
                                       ) -> tuple[SchedulingModeration.Category, bool]:
    scheduling_sources = get_scheduling_sources(scheduling)
    if not scheduling_sources.parsings and not scheduling_sources.oclocher_schedules:
        moderation_validated = has_crawling_moderation_been_validated(scheduling)
        return SchedulingModeration.Category.NO_SOURCE, moderation_validated

    if not index_events:
        return SchedulingModeration.Category.NO_SCHEDULE, False

    # TODO add UNKNOWN_PLACE

    if website_has_schedules_conflict(index_events):
        return SchedulingModeration.Category.SCHEDULES_CONFLICT, False

    return SchedulingModeration.Category.OK, False


def add_necessary_scheduling_moderation(scheduling: Scheduling, index_events: list[IndexEvent]):
    category, moderation_validated = get_scheduling_moderation_category(scheduling, index_events)
    upsert_scheduling_moderation(scheduling.website, category, moderation_validated)
