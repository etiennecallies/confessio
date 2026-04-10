from django.conf import settings

from core.utils.discord_utils import send_discord_alert, DiscordChanel
from core.views import get_moderation_url
from crawling.models import CrawlingModeration
from registry.models import Website
from registry.models.base_moderation_models import ModerationStatus
from scheduling.models import Scheduling
from scheduling.models.scheduling_moderation_models import SchedulingModeration, \
    ValidatedSchedulesModeration
from scheduling.services.merging.schedules_conflict_service import website_has_schedules_conflict
from scheduling.services.scheduling.index_scheduling_service import SchedulingIndexingObjects
from scheduling.services.scheduling.scheduling_service import get_scheduling_sources


#########################
# SCHEDULING MODERATION #
#########################

def upsert_scheduling_moderation(website: Website, category: SchedulingModeration.Category,
                                 moderation_validated: bool):
    try:
        moderation = SchedulingModeration.objects.get(website=website)
        if moderation.category != category:
            moderation.category = category
            moderation.status = (ModerationStatus.VALIDATED
                                 if moderation_validated
                                 else ModerationStatus.TO_VALIDATE)
            moderation.save()
    except SchedulingModeration.DoesNotExist:
        moderation = SchedulingModeration(
            website=website, category=category,
            diocese=website.get_diocese(),
            status=(ModerationStatus.VALIDATED
                    if moderation_validated
                    else ModerationStatus.TO_VALIDATE),
        )
        moderation.save()


def has_crawling_moderation_been_validated(scheduling: Scheduling) -> bool:
    return CrawlingModeration.objects.filter(
        website=scheduling.website,
        category__in=[CrawlingModeration.Category.NO_RESPONSE, CrawlingModeration.Category.NO_PAGE],
        status=ModerationStatus.VALIDATED,
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


##################################
# VALIDATED SCHEDULES MODERATION #
##################################

def notify_if_relevant(moderation: ValidatedSchedulesModeration,):
    if moderation.category == ValidatedSchedulesModeration.Category.OK:
        return

    moderation_url = settings.REQUEST_BASE_URL + get_moderation_url(moderation)
    send_discord_alert(f"Schedules differ "
                       f"on website {moderation.website.name} "
                       f"{moderation_url}",
                       DiscordChanel.NEW_SCHEDULES)


def upsert_validated_schedules_moderation(website: Website,
                                          category: ValidatedSchedulesModeration.Category,
                                          moderation_validated: bool):
    try:
        moderation = ValidatedSchedulesModeration.objects.get(website=website)
        if moderation.category != category:
            moderation.category = category
            moderation.status = (ModerationStatus.VALIDATED
                                 if moderation_validated
                                 else ModerationStatus.TO_VALIDATE)
            moderation.save()
            notify_if_relevant(moderation)
    except ValidatedSchedulesModeration.DoesNotExist:
        moderation = ValidatedSchedulesModeration(
            website=website, category=category,
            diocese=website.get_diocese(),
            status=(ModerationStatus.VALIDATED
                    if moderation_validated
                    else ModerationStatus.TO_VALIDATE),
        )
        moderation.save()
        notify_if_relevant(moderation)


def get_validated_schedules_moderation_category(
        indexing_objects: SchedulingIndexingObjects
) -> tuple[ValidatedSchedulesModeration.Category, bool] | None:
    if indexing_objects.schedules_match_with_validated is None:
        return None

    if not indexing_objects.schedules_match_with_validated:
        return ValidatedSchedulesModeration.Category.SCHEDULES_DIFFERS, False

    return ValidatedSchedulesModeration.Category.OK, True


def handle_validated_schedules_moderation(scheduling: Scheduling,
                                          indexing_objects: SchedulingIndexingObjects):
    category_and_validation = get_validated_schedules_moderation_category(indexing_objects)
    if category_and_validation is None:
        return
    category, moderation_validated = category_and_validation
    upsert_validated_schedules_moderation(scheduling.website, category, moderation_validated)


########
# MAIN #
########

def add_necessary_scheduling_moderation(scheduling: Scheduling,
                                        indexing_objects: SchedulingIndexingObjects):
    handle_scheduling_moderation(scheduling, indexing_objects)
    handle_validated_schedules_moderation(scheduling, indexing_objects)
