from django.contrib.auth.models import User
from django.db.models.functions import Now

from registry.models import Website
from scheduling.models import WebsiteSchedules
from scheduling.public_model import SourcedSchedulesList
from scheduling.services.scheduling.scheduling_service import get_indexed_scheduling
from scheduling.workflows.merging.sourced_schedules import SourcedScheduleItem
from scheduling.workflows.merging.sources import ParsingSource
from scheduling.workflows.parsing.schedules import ScheduleItem


def has_parsing_source(sourced_schedule_item: SourcedScheduleItem) -> bool:
    for source in sourced_schedule_item.sources:
        if isinstance(source, ParsingSource):
            return True

    return False


def get_schedule_items(sourced_schedules_list: SourcedSchedulesList) -> set[ScheduleItem]:
    schedule_items = set()
    for sourced_schedule_of_church in sourced_schedules_list.sourced_schedules_of_churches:
        for sourced_schedule_item in sourced_schedule_of_church.sourced_schedules:
            if not has_parsing_source(sourced_schedule_item):
                continue

            schedule_items.add(sourced_schedule_item.item)

    return schedule_items


def check_schedules_match(website: Website,
                          sourced_schedules_list: SourcedSchedulesList) -> bool | None:
    try:
        website_schedules = website.schedules
    except WebsiteSchedules.DoesNotExist:
        return None

    validated_sourced_schedules_list = \
        SourcedSchedulesList(**website_schedules.validated_sourced_schedules_list)

    return get_schedule_items(validated_sourced_schedules_list) == \
        get_schedule_items(sourced_schedules_list)


def validate_website_indexed_schedules(website: Website, user: User):
    scheduling = get_indexed_scheduling(website)
    if scheduling is None:
        print(f'No indexed scheduling found for {website}')
        return

    try:
        website_schedules = website.schedules
        website_schedules.validated_sourced_schedules_list = scheduling.sourced_schedules_list
        website_schedules.validated_at = Now()
        website_schedules.validated_by = user
    except WebsiteSchedules.DoesNotExist:
        website_schedules = WebsiteSchedules(
            website=website,
            validated_sourced_schedules_list=scheduling.sourced_schedules_list,
            validated_at=Now(),
            validated_by=user
        )

    website_schedules.save()
