from datetime import datetime

from django.template.defaulttags import register

from home.models import WebsiteModeration, ChurchModeration, ParishModeration, \
    PruningModeration, SentenceModeration, ParsingModeration, Website
from home.services.events_service import ChurchSchedulesList, \
    get_merged_church_schedules_list
from scraping.parse.schedules import ScheduleItem, Event
from scraping.parse.test_rrule import get_events_from_schedule_item


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def negate(value):
    return not value


@register.filter
def get_church_schedules_list(website: Website) -> ChurchSchedulesList:
    church_schedules_lists = [ChurchSchedulesList.from_parsing(parsing)
                              for parsing in website.get_all_parsings()]
    return get_merged_church_schedules_list([csl for csl in church_schedules_lists
                                             if csl is not None])


@register.filter
def get_schedule_item_events(schedule_item: ScheduleItem) -> list[Event]:
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2040, 1, 1)

    return get_events_from_schedule_item(schedule_item, start_date, end_date)[:7]


@register.simple_tag
def get_moderation_stats():
    return sum([
        WebsiteModeration.get_stats_by_category(),
        ParishModeration.get_stats_by_category(),
        ChurchModeration.get_stats_by_category(),
        PruningModeration.get_stats_by_category(),
        SentenceModeration.get_stats_by_category(),
        ParsingModeration.get_stats_by_category(),
    ], [])
