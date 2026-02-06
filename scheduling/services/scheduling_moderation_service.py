from registry.models import Website
from scheduling.models import Scheduling
from scheduling.models.scheduling_moderation_models import SchedulingModeration
from scheduling.services.scheduling_service import get_scheduling_sources


def upsert_scheduling_moderation(website: Website, category: SchedulingModeration.Category):
    try:
        moderation = SchedulingModeration.objects.get(website=website)
        if moderation.category != category:
            moderation.category = category
            moderation.save()
    except SchedulingModeration.DoesNotExist:
        moderation = SchedulingModeration(
            website=website, category=category,
            diocese=website.get_diocese(),
        )
        moderation.save()


def get_scheduling_moderation_category(scheduling: Scheduling) -> SchedulingModeration.Category:
    scheduling_sources = get_scheduling_sources(scheduling)
    if not scheduling_sources.parsings and not scheduling_sources.oclocher_schedules:
        return SchedulingModeration.Category.NO_SOURCE

    # TODO add more catagories here

    return SchedulingModeration.Category.OK


def add_necessary_scheduling_moderation(scheduling: Scheduling):
    category = get_scheduling_moderation_category(scheduling)
    upsert_scheduling_moderation(scheduling.website, category)
