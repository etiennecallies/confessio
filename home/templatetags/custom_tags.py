from datetime import datetime
from typing import Optional

from django.template.defaulttags import register
from django.urls import reverse

from home.models import WebsiteModeration, ChurchModeration, ParishModeration, \
    PruningModeration, SentenceModeration, ParsingModeration, ModerationMixin, Pruning, \
    Page, Parsing, ReportModeration, Diocese
from home.utils.date_utils import get_current_year
from home.utils.list_utils import enumerate_with_and
from scraping.parse.rrule_utils import get_events_from_schedule_item
from scraping.parse.schedules import ScheduleItem, Event, SchedulesList


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def negate(value):
    return not value


@register.filter
def get_schedule_item_events(schedule_item: ScheduleItem) -> list[Event]:
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2040, 1, 1)
    default_year = get_current_year()

    return get_events_from_schedule_item(schedule_item, start_date, end_date, default_year)[:7]


@register.filter
def has_relation_text(schedules_list: SchedulesList | None) -> str:
    if not schedules_list:
        return ''

    relations = []
    if schedules_list.is_related_to_mass:
        relations.append('messes')
    if schedules_list.is_related_to_adoration:
        relations.append('adorations')
    if schedules_list.is_related_to_permanence:
        relations.append('permanences')
    if relations:
        relation_text = enumerate_with_and(relations)

        return f'👉 Certaines horaires sont liées aux {relation_text} (voir sources).'

    return ''


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
    return list(Diocese.objects.all()) + [None]


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
