from django.template.defaulttags import register

from home.models import WebsiteModeration, ChurchModeration, ParishModeration, \
    PruningModeration, SentenceModeration, ParsingModeration, Website
from home.services.events_service import ChurchSchedulesList, \
    get_merged_church_schedules_list


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def negate(value):
    return not value


@register.filter
def get_church_schedules_list(website: Website) -> ChurchSchedulesList:
    church_schedules_lists = [ChurchSchedulesList.from_parsing(parsing)
                              for parsing in website.parsings.all()]
    return get_merged_church_schedules_list(church_schedules_lists)


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
