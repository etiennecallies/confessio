from uuid import UUID

from crawling.models import CrawlingModeration
from registry.models import Website
from scheduling.models import SchedulingModeration, ValidatedSchedulesModeration


def get_all_website_moderations(websites: list[Website]
                                ) -> tuple[
    dict[UUID, SchedulingModeration],
    dict[UUID, CrawlingModeration],
    dict[UUID, ValidatedSchedulesModeration],
]:
    all_scheduling_moderations = SchedulingModeration.objects.filter(website__in=websites).all()
    scheduling_moderation_by_website = {}
    for scheduling_moderation in all_scheduling_moderations:
        scheduling_moderation_by_website[scheduling_moderation.website.uuid] = scheduling_moderation

    all_crawling_moderations = CrawlingModeration.objects.filter(website__in=websites).all()
    crawling_moderation_by_website = {}
    for crawling_moderation in all_crawling_moderations:
        crawling_moderation_by_website[crawling_moderation.website.uuid] = crawling_moderation

    all_website_schedules_moderations = ValidatedSchedulesModeration.objects\
        .filter(website__in=websites).all()
    website_schedules_moderation_by_website = {}
    for website_schedules_moderation in all_website_schedules_moderations:
        website_schedules_moderation_by_website[website_schedules_moderation.website.uuid] = \
            website_schedules_moderation

    return scheduling_moderation_by_website, crawling_moderation_by_website, \
        website_schedules_moderation_by_website
