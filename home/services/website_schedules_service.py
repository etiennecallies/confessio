from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional, Callable
from uuid import UUID

from home.models import Church, Website
from home.services.holiday_zone_service import get_website_holiday_zone
from home.services.sources_service import get_website_sorted_parsings
from home.utils.date_utils import get_current_year
from home.utils.hash_utils import hash_string_to_hex
from scheduling.models import Scheduling
from scheduling.models.parsing_models import Parsing
from scraping.parse.explain_schedule import schedule_item_sort_key, get_explanation_from_schedule
from scraping.parse.liturgical import PeriodEnum
from scraping.parse.rrule_utils import get_events_from_schedule_item
from scraping.parse.schedules import Event, ScheduleItem, WeeklyRule, RegularRule, CustomPeriod
from scraping.services.parsing_service import get_church_by_id, get_parsing_schedules_list


#############
# SCHEDULES #
#############

@dataclass
class ParsingScheduleItem:
    item: ScheduleItem
    explanation: str
    parsing_uuids: list[UUID]
    events: list[Event]


@dataclass
class ChurchScheduleItem:
    church: Optional[Church]
    is_church_explicitly_other: bool
    schedule_item: ParsingScheduleItem

    @classmethod
    def from_schedule_item(cls, schedule_item: ScheduleItem, parsing: Parsing,
                           church_by_id: dict[int, Church], events: list[Event]
                           ) -> 'ChurchScheduleItem':
        parsing_schedule_item = ParsingScheduleItem(schedule_item,
                                                    get_explanation_from_schedule(schedule_item),
                                                    [parsing.uuid], events)
        if schedule_item.church_id is None or schedule_item.church_id == -1:
            return cls(
                church=None,
                is_church_explicitly_other=schedule_item.church_id == -1,
                schedule_item=parsing_schedule_item,
            )

        return cls(
            church=church_by_id[schedule_item.church_id],
            is_church_explicitly_other=False,
            schedule_item=parsing_schedule_item,
        )


@dataclass
class ChurchSortedSchedules:
    church: Optional[Church]
    is_church_explicitly_other: bool
    sorted_schedules: list[ParsingScheduleItem]

    @classmethod
    def from_sorted_schedules(cls, church_schedules: list[ChurchScheduleItem],
                              church_id: int | None,
                              church_by_id: dict[int, Church]) -> 'ChurchSortedSchedules':
        return cls(
            church=church_by_id[church_id] if church_id is not None and church_id != -1 else None,
            is_church_explicitly_other=church_id == -1,
            sorted_schedules=[church_schedule.schedule_item
                              for church_schedule in church_schedules],
        )


@dataclass
class WebsiteSchedules:
    church_sorted_schedules: list[ChurchSortedSchedules]
    possible_by_appointment_parsings: list[Parsing]
    is_related_to_mass_parsings: list[Parsing]
    is_related_to_adoration_parsings: list[Parsing]
    is_related_to_permanence_parsings: list[Parsing]
    will_be_seasonal_events_parsings: list[Parsing]
    source_index_by_parsing_uuid: dict[UUID, int]
    parsing_by_uuid: dict[UUID, Parsing]
    church_color_by_uuid: dict[UUID, str]


def get_website_schedules(website: Website,
                          all_website_churches: list[Church],
                          max_days: int = 1,
                          parsings: list[Parsing] | None = None,
                          ) -> WebsiteSchedules:
    ################
    # Get parsings #
    ################
    all_church_schedule_items = []

    possible_by_appointment_parsings = []
    is_related_to_mass_parsings = []
    is_related_to_adoration_parsings = []
    is_related_to_permanence_parsings = []
    will_be_seasonal_events_parsings = []

    start_date = date.today()
    current_year = get_current_year()
    end_date = start_date + timedelta(days=300)

    holiday_zone = get_website_holiday_zone(website, all_website_churches)

    if parsings is None:
        scheduling = website.schedulings.filter(status=Scheduling.Status.INDEXED).first()
        if scheduling is None:
            parsings = []
        else:
            parsings = get_website_sorted_parsings(scheduling)

    for i, parsing in enumerate(parsings):
        church_by_id = get_church_by_id(parsing, all_website_churches)

        schedules_list = get_parsing_schedules_list(parsing)
        if schedules_list is None:
            continue

        for schedule in schedules_list.schedules:
            if schedule.church_id is not None and schedule.church_id != -1 \
                    and schedule.church_id not in church_by_id:
                # We ignore schedule for out of scope churches
                # TODO can it happen?
                continue

            events = get_events_from_schedule_item(schedule, start_date,
                                                   current_year, holiday_zone,
                                                   end_date, max_days=max_days)
            if events:
                all_church_schedule_items.append(
                    ChurchScheduleItem.from_schedule_item(schedule, parsing, church_by_id, events)
                )

        if schedules_list.possible_by_appointment:
            possible_by_appointment_parsings.append(parsing)
        if schedules_list.is_related_to_mass:
            is_related_to_mass_parsings.append(parsing)
        if schedules_list.is_related_to_adoration:
            is_related_to_adoration_parsings.append(parsing)
        if schedules_list.is_related_to_permanence:
            is_related_to_permanence_parsings.append(parsing)
        if schedules_list.will_be_seasonal_events:
            will_be_seasonal_events_parsings.append(parsing)

    merged_church_schedule_items = get_merged_schedule_items(all_church_schedule_items)
    # TODO we shall make sure the church_id are the same across all parsings
    church_by_id = {cs.schedule_item.item.church_id: cs.church
                    for cs in merged_church_schedule_items}

    ######################
    # Get schedule_items #
    ######################

    church_schedule_items = get_sorted_schedules_by_church_id(merged_church_schedule_items)
    church_sorted_schedules = [
        ChurchSortedSchedules.from_sorted_schedules(church_schedules, church_id, church_by_id)
        for church_id, church_schedules in church_schedule_items.items()
    ]

    # Add churches without events
    churches_with_events = {cs.church for cs in merged_church_schedule_items}
    church_sorted_schedules += [
        ChurchSortedSchedules(
            church=c,
            is_church_explicitly_other=False,
            sorted_schedules=[]
        ) for c in all_website_churches if c not in churches_with_events
    ]

    source_index_by_parsing_uuid = {source.uuid: i for i, source in enumerate(parsings)}
    parsing_by_uuid = {parsing.uuid: parsing for parsing in parsings}

    return WebsiteSchedules(
        church_sorted_schedules=church_sorted_schedules,
        possible_by_appointment_parsings=possible_by_appointment_parsings,
        is_related_to_mass_parsings=is_related_to_mass_parsings,
        is_related_to_adoration_parsings=is_related_to_adoration_parsings,
        is_related_to_permanence_parsings=is_related_to_permanence_parsings,
        will_be_seasonal_events_parsings=will_be_seasonal_events_parsings,
        source_index_by_parsing_uuid=source_index_by_parsing_uuid,
        parsing_by_uuid=parsing_by_uuid,
        church_color_by_uuid=get_church_color_by_uuid(church_sorted_schedules),
    )


##########
# COLORS #
##########

def get_church_color_by_uuid(church_sorted_schedules: list[ChurchSortedSchedules]
                             ) -> dict[UUID, str]:
    church_color_by_uuid = {}
    index = 0
    for church_schedule in church_sorted_schedules:
        if church_schedule.church:
            church_color_by_uuid[church_schedule.church.uuid] = get_church_color(index)
            index += 1

    return church_color_by_uuid


def get_church_color(church_index: int) -> str:
    if church_index == 0:
        return '#C0EDF2'

    if church_index == 1:
        return '#B7E7CC'

    if church_index == 2:
        return '#E4D8F3'

    # Generate a hash of the string
    hash_hex = hash_string_to_hex(str(church_index))

    # Convert first 3 bytes of hash to RGB values
    r = int(hash_hex[:2], 16)
    g = int(hash_hex[2:4], 16)
    b = int(hash_hex[4:6], 16)

    # Convert to pastel by mixing with white
    # This ensures colors are always light and pleasant
    pastel_factor = 0.6  # Higher value = lighter colors

    r = int(r + (255 - r) * pastel_factor)
    g = int(g + (255 - g) * pastel_factor)
    b = int(b + (255 - b) * pastel_factor)

    # Convert to hex color code
    return f"#{r:02x}{g:02x}{b:02x}"


def get_no_church_color(is_church_explicitly_other: bool) -> str:
    return '#E8A5B3' if is_church_explicitly_other else 'lightgray'


def get_color_of_nullable_church(church: Church | None,
                                 church_color_by_uuid: dict[UUID, str],
                                 is_church_explicitly_other: bool) -> str:
    if church:
        return church_color_by_uuid[church.uuid]

    return get_no_church_color(is_church_explicitly_other)


#########
# MERGE #
#########

def get_periods_or_custom_periods_key(periods: list[PeriodEnum | CustomPeriod]) -> tuple:
    return (
        tuple(sorted(p for p in periods if isinstance(p, PeriodEnum))),
        tuple(sorted(p for p in periods if isinstance(p, CustomPeriod)))
    )


def merge_similar_weekly_rules_of_church(church_schedule_items: list[ChurchScheduleItem]
                                         ) -> list[ChurchScheduleItem]:
    results = []
    schedules_by_key = {}
    for church_schedule_item in church_schedule_items:
        date_rule = church_schedule_item.schedule_item.item.date_rule
        if not church_schedule_item.schedule_item.item.is_regular_rule() or \
                not date_rule.is_weekly_rule():
            results.append(church_schedule_item)
            continue

        key = (
            church_schedule_item.schedule_item.item.is_cancellation,
            church_schedule_item.schedule_item.item.start_time_iso8601,
            church_schedule_item.schedule_item.item.end_time_iso8601,
            get_periods_or_custom_periods_key(date_rule.only_in_periods),
            get_periods_or_custom_periods_key(date_rule.not_in_periods),
            tuple(sorted(date_rule.not_on_dates)),
        )
        schedules_by_key.setdefault(key, []).append(church_schedule_item)

    for schedules_group in schedules_by_key.values():
        first_schedule = schedules_group[0]
        if len(schedules_group) == 1:
            results.append(first_schedule)
            continue

        combined_weekdays_days = set()
        for church_schedule_item in schedules_group:
            combined_weekdays_days.update(
                church_schedule_item.schedule_item.item.date_rule.rule.by_weekdays)

        first_item = first_schedule.schedule_item.item
        combined_schedule_item = ScheduleItem(
            church_id=first_item.church_id,
            date_rule=RegularRule(
                rule=WeeklyRule(by_weekdays=list(combined_weekdays_days)),
                only_in_periods=first_item.date_rule.only_in_periods,
                not_in_periods=first_item.date_rule.not_in_periods,
                not_on_dates=first_item.date_rule.not_on_dates,
            ),
            is_cancellation=first_item.is_cancellation,
            start_time_iso8601=first_item.start_time_iso8601,
            end_time_iso8601=first_item.end_time_iso8601,
        )

        parsing_uuids = list(set(sum((cs.schedule_item.parsing_uuids for cs in schedules_group),
                                     [])))
        combined_events = list(sorted(set(sum(
            (cs.schedule_item.events for cs in schedules_group), []))))

        combined_parsing_schedule_item = ParsingScheduleItem(
            item=combined_schedule_item,
            explanation=get_explanation_from_schedule(combined_schedule_item),
            parsing_uuids=parsing_uuids,
            events=combined_events
        )

        combined_church_schedule_item = ChurchScheduleItem(
            church=first_schedule.church,
            is_church_explicitly_other=first_schedule.is_church_explicitly_other,
            schedule_item=combined_parsing_schedule_item
        )

        results.append(combined_church_schedule_item)

    return results


def apply_on_same_church(
        church_schedule_items: list[ChurchScheduleItem],
        function_on_group: Callable[[list[ChurchScheduleItem]], list[ChurchScheduleItem]]
) -> list[ChurchScheduleItem]:
    church_schedule_items_by_church = {}
    for church_schedule_item in church_schedule_items:
        church_schedule_items_by_church.setdefault(
            church_schedule_item.schedule_item.item.church_id, []).append(church_schedule_item)

    church_schedule_items = []
    for church_schedule_items_group in church_schedule_items_by_church.values():
        church_schedule_items.extend(
            function_on_group(church_schedule_items_group)
        )

    return church_schedule_items


def eliminate_similar_with_unknow_church(church_schedule_items: list[ChurchScheduleItem]
                                         ) -> list[ChurchScheduleItem]:
    church_explanations = set()
    for church_schedule_item in church_schedule_items:
        if church_schedule_item.church:
            church_explanations.add(church_schedule_item.schedule_item.explanation)

    schedules_by_explanation_and_item = {}
    for church_schedule_item in church_schedule_items:
        if church_schedule_item.church or \
                church_schedule_item.schedule_item.explanation not in church_explanations:
            # We ignore church_schedule_item with no church and with real-church explanation
            schedules_by_explanation_and_item.setdefault(
                (
                    church_schedule_item.church,
                    church_schedule_item.is_church_explicitly_other,
                    church_schedule_item.schedule_item.explanation,
                ), []).append(church_schedule_item)

    merged_schedules_items = []
    for schedules_group in schedules_by_explanation_and_item.values():
        parsing_uuids = list(set(sum((cs.schedule_item.parsing_uuids for cs in schedules_group),
                                     [])))
        merged_schedule = ChurchScheduleItem(
            church=schedules_group[0].church,
            is_church_explicitly_other=schedules_group[0].is_church_explicitly_other,
            schedule_item=ParsingScheduleItem(
                item=schedules_group[0].schedule_item.item,
                explanation=schedules_group[0].schedule_item.explanation,
                parsing_uuids=parsing_uuids,
                events=schedules_group[0].schedule_item.events
            )
        )
        merged_schedules_items.append(merged_schedule)

    return merged_schedules_items


def eliminate_similar_without_exception_of_church(church_schedule_items: list[ChurchScheduleItem]
                                                  ) -> list[ChurchScheduleItem]:
    explanations_dict = {}
    for church_schedule_item in church_schedule_items:
        item = church_schedule_item.schedule_item.item
        if item.is_one_off_rule():
            continue

        if item.date_rule.only_in_periods or \
                item.date_rule.not_in_periods or \
                item.date_rule.not_on_dates:
            schedule_item_without_exception = item.model_copy(
                update={
                    'date_rule': item.date_rule.model_copy(
                        update={
                            'only_in_periods': [],
                            'not_in_periods': [],
                            'not_on_dates': [],
                        }
                    )
                }
            )
            explanation_without_exceptions = get_explanation_from_schedule(
                schedule_item_without_exception)
            explanations_dict.setdefault(explanation_without_exceptions, [])\
                .append(church_schedule_item)

    results = []
    for church_schedule_item in church_schedule_items:
        item = church_schedule_item.schedule_item.item
        if item.is_one_off_rule():
            results.append(church_schedule_item)
            continue

        if not item.date_rule.only_in_periods and \
                not item.date_rule.not_in_periods and \
                not item.date_rule.not_on_dates:
            if church_schedule_item.schedule_item.explanation in explanations_dict \
                    and len(explanations_dict[church_schedule_item.schedule_item.explanation]) == 1:
                # We keep church_schedule_item with exception
                continue

        results.append(church_schedule_item)

    return results


def get_merged_schedule_items(church_schedule_items: list[ChurchScheduleItem]
                              ) -> list[ChurchScheduleItem]:
    # First we merge weekly rules when possible
    church_schedule_items = apply_on_same_church(church_schedule_items,
                                                 merge_similar_weekly_rules_of_church)

    # Then we eliminate similar schedule_items with unknow church
    church_schedule_items = eliminate_similar_with_unknow_church(church_schedule_items)

    # Finally we eliminate similar schedule_items without exception
    church_schedule_items = apply_on_same_church(church_schedule_items,
                                                 eliminate_similar_without_exception_of_church)

    return church_schedule_items


########
# SORT #
########

def church_schedule_item_sort_key(church_schedule_item: ChurchScheduleItem) -> tuple:
    return schedule_item_sort_key(church_schedule_item.schedule_item.item)


def get_sorted_schedules_by_church_id(church_schedules: list[ChurchScheduleItem]
                                      ) -> dict[int, list[ChurchScheduleItem]]:
    sorted_schedules_by_church_id = {}

    for church_schedule in sorted(church_schedules, key=church_schedule_item_sort_key):
        sorted_schedules_by_church_id.setdefault(church_schedule.schedule_item.item.church_id, [])\
            .append(church_schedule)

    return sorted_schedules_by_church_id
