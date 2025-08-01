from datetime import date
from typing import Optional

from django.template.defaulttags import register
from django.urls import reverse

from home.models import WebsiteModeration, ChurchModeration, ParishModeration, \
    PruningModeration, SentenceModeration, ParsingModeration, ModerationMixin, Pruning, \
    Page, Parsing, ReportModeration, Diocese
from home.services.website_events_service import WebsiteEvents
from home.services.website_schedules_service import WebsiteSchedules
from home.utils.date_utils import get_current_year
from home.utils.list_utils import enumerate_with_and
from scraping.parse.holidays import HolidayZoneEnum
from scraping.parse.rrule_utils import get_events_from_schedule_item
from scraping.parse.schedules import ScheduleItem, Event


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_item_str(dictionary, key):
    return dictionary.get(str(key))


@register.filter
def days_of_range(website_events: WebsiteEvents,
                  range_number_as_str: str) -> list[date]:
    sorted_days = sorted(website_events.church_events_by_day.keys())
    nb_days = 4
    range_number = int(range_number_as_str) - 1

    return sorted_days[range_number * nb_days:(range_number + 1) * nb_days]


@register.filter
def subtract(v1, v2):
    return v1 - v2


@register.filter
def get_ith(some_list: list, i):
    return some_list[i]


@register.filter
def negate(value):
    return not value


@register.filter
def get_schedule_item_events(schedule_item: ScheduleItem) -> list[Event]:
    start_date = date(2000, 1, 1)
    end_date = date(2040, 1, 1)
    default_year = get_current_year()
    default_holiday_zone = HolidayZoneEnum.FR_ZONE_A

    return get_events_from_schedule_item(schedule_item, start_date, default_year,
                                         default_holiday_zone, end_date)[:7]


@register.filter
def has_relation_text(website_schedules: WebsiteSchedules | None) -> str:
    if not website_schedules:
        return ''

    relations = []
    if website_schedules.is_related_to_mass_parsings:
        relations.append('messes')
    if website_schedules.is_related_to_adoration_parsings:
        relations.append('adorations')
    if website_schedules.is_related_to_permanence_parsings:
        relations.append('permanences')

    if relations:
        relation_text = enumerate_with_and(relations)

        return f'👉 Certaines horaires sont liées aux {relation_text}'

    return ''


@register.filter
def relation_parsing_uuids(website_schedules: WebsiteSchedules | None
                           ) -> list[int]:
    if not website_schedules:
        return []

    return list(set(
        map(lambda parsing: parsing.uuid,
            website_schedules.is_related_to_mass_parsings
            + website_schedules.is_related_to_adoration_parsings
            + website_schedules.is_related_to_permanence_parsings)
    ))


@register.filter
def get_url(moderation: ModerationMixin):
    return reverse(f'moderate_one_' + moderation.resource,
                   kwargs={
                       'category': moderation.category,
                       'is_bug': moderation.marked_as_bug_at is not None,
                       'moderation_uuid': moderation.uuid,
                       'diocese_slug': moderation.get_diocese_slug(),
                   })


@register.filter
def get_unvalidated_pruning_moderation(pruning: Pruning) -> Optional[PruningModeration]:
    try:
        return pruning.moderations.filter(validated_at__isnull=True).get()
    except PruningModeration.DoesNotExist:
        return None


@register.filter
def get_page_parsing_of_pruning(page: Page, pruning: Pruning) -> Optional[Parsing]:
    return page.get_parsing(pruning)


@register.simple_tag
def get_dioceses() -> list[Diocese | None]:
    return [None] + list(Diocese.objects.all())


@register.filter
def get_moderation_stats(diocese: Diocese | None):
    return sum([
        WebsiteModeration.get_stats_by_category(diocese),
        ParishModeration.get_stats_by_category(diocese),
        ChurchModeration.get_stats_by_category(diocese),
        PruningModeration.get_stats_by_category(diocese),
        SentenceModeration.get_stats_by_category(diocese),
        ParsingModeration.get_stats_by_category(diocese),
        ReportModeration.get_stats_by_category(diocese),
    ], [])
