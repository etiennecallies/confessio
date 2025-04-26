from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from home.models import Church, Parsing, Website
from home.services.holiday_zone_service import get_website_holiday_zone
from home.services.sources_service import get_website_sorted_parsings
from home.utils.date_utils import get_current_year, time_from_minutes
from home.utils.hash_utils import hash_string_to_hex
from scraping.parse.explain_schedule import schedule_item_sort_key, get_explanation_from_schedule
from scraping.parse.rrule_utils import get_events_from_schedule_item
from scraping.parse.schedules import Event, ScheduleItem
from scraping.services.parsing_service import get_church_by_id, get_parsing_schedules_list


########################
# EVENTS AND SCHEDULES #
########################

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
class ChurchEvent:
    church: Optional[Church]
    is_church_explicitly_other: bool
    event: Event

    @classmethod
    def from_event(cls, event: Event, church_by_id: dict[int, Church]) -> 'ChurchEvent':
        if event.church_id is None or event.church_id == -1:
            return cls(
                church=None,
                is_church_explicitly_other=event.church_id == -1,
                event=event,
            )

        return cls(
            church=church_by_id[event.church_id],
            is_church_explicitly_other=False,
            event=event,
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
class MergedChurchSchedulesList:
    church_events_by_day: dict[date, list[ChurchEvent]]
    church_sorted_schedules: list[ChurchSortedSchedules]
    possible_by_appointment_parsings: list[Parsing]
    is_related_to_mass_parsings: list[Parsing]
    is_related_to_adoration_parsings: list[Parsing]
    is_related_to_permanence_parsings: list[Parsing]
    will_be_seasonal_events_parsings: list[Parsing]
    source_index_by_parsing_uuid: dict[UUID, int]
    parsings_have_been_moderated: bool
    church_color_by_uuid: dict[UUID, str]
    display_explicit_other_churches: bool
    has_explicit_other_churches: bool
    has_unknown_churches: bool
    has_different_churches: bool


def get_merged_church_schedules_list(website: Website,
                                     all_website_churches: list[Church],
                                     day_filter: date | None = None,
                                     hour_min: int | None = None,
                                     hour_max: int | None = None,
                                     max_days: int = 8
                                     ) -> MergedChurchSchedulesList:
    ################
    # Get parsings #
    ################
    all_church_schedule_items = []

    possible_by_appointment_parsings = []
    is_related_to_mass_parsings = []
    is_related_to_adoration_parsings = []
    is_related_to_permanence_parsings = []
    will_be_seasonal_events_parsings = []

    if not day_filter:
        start_date = date.today()
        current_year = get_current_year()
        end_date = start_date + timedelta(days=300)
    else:
        start_date = day_filter
        current_year = start_date.year
        end_date = start_date
        max_days = 1

    min_time = max_time = None
    if hour_min or hour_max:
        min_time = time_from_minutes(hour_min or 0)
        max_time = time_from_minutes(hour_max or 24 * 60 - 1)

    holiday_zone = get_website_holiday_zone(website, all_website_churches)

    if website.unreliability_reason:
        parsings = []
    else:
        parsings = get_website_sorted_parsings(website)

    for i, parsing in enumerate(parsings):
        church_by_id = get_church_by_id(parsing, all_website_churches)

        schedules_list = get_parsing_schedules_list(parsing)
        if schedules_list is None:
            continue

        for schedule in schedules_list.schedules:
            if schedule.church_id is not None and schedule.church_id != -1 \
                    and schedule.church_id not in church_by_id:
                # We ignore schedule for out of scope churches
                continue

            if min_time or max_time:
                start_time = schedule.get_start_time() or min_time
                end_time = schedule.get_end_time() or max_time
                if start_time > max_time or end_time < min_time:
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

    ##############
    # Get events #
    ##############

    all_events = list(sorted(list(set(
        sum((cs.schedule_item.events for cs in merged_church_schedule_items), [])))))

    church_events_by_day = {}
    if all_events:
        first_day = all_events[0].start.date()
        for i in range(max_days):
            day = first_day + timedelta(days=i)
            church_events_by_day[day] = []

        for event in all_events:
            event_date = event.start.date()
            if event_date in church_events_by_day:
                church_event = ChurchEvent.from_event(event, church_by_id)
                church_events_by_day[event_date].append(church_event)

    ######################
    # Get schedule_items #
    ######################

    church_schedule_items = get_sorted_schedules_by_church_id(merged_church_schedule_items)
    church_sorted_schedules = [
        ChurchSortedSchedules.from_sorted_schedules(church_schedules, church_id, church_by_id)
        for church_id, church_schedules in church_schedule_items.items()
    ]

    churches_with_events = {cs.church for cs in merged_church_schedule_items}
    church_sorted_schedules += [
        ChurchSortedSchedules(
            church=c,
            is_church_explicitly_other=False,
            sorted_schedules=[]
        ) for c in all_website_churches if c not in churches_with_events
    ]

    source_index_by_parsing_uuid = {source.uuid: i for i, source in enumerate(parsings)}
    parsings_have_been_moderated = all(parsing.has_been_moderated() for parsing in parsings)
    display_explicit_other_churches = do_display_explicit_other_churches(church_sorted_schedules)
    all_church_events = sum(church_events_by_day.values(), [])
    has_explicit_other_churches = display_explicit_other_churches and \
        any(c.is_church_explicitly_other for c in all_church_events)
    has_unknown_churches = any(c.church is None and not c.is_church_explicitly_other
                               for c in all_church_events)
    has_different_churches = len(set(c.church for c in all_church_events if c.church)) > 1

    return MergedChurchSchedulesList(
        church_events_by_day=church_events_by_day,
        church_sorted_schedules=church_sorted_schedules,
        possible_by_appointment_parsings=possible_by_appointment_parsings,
        is_related_to_mass_parsings=is_related_to_mass_parsings,
        is_related_to_adoration_parsings=is_related_to_adoration_parsings,
        is_related_to_permanence_parsings=is_related_to_permanence_parsings,
        will_be_seasonal_events_parsings=will_be_seasonal_events_parsings,
        source_index_by_parsing_uuid=source_index_by_parsing_uuid,
        parsings_have_been_moderated=parsings_have_been_moderated,
        church_color_by_uuid=get_church_color_by_uuid(church_sorted_schedules),
        display_explicit_other_churches=display_explicit_other_churches,
        has_explicit_other_churches=has_explicit_other_churches,
        has_unknown_churches=has_unknown_churches,
        has_different_churches=has_different_churches,
    )


#####################################
# DECIDE ON EXPLICIT OTHER CHURCHES #
#####################################

def do_display_explicit_other_churches(church_sorted_schedules: list[ChurchSortedSchedules]
                                       ) -> bool:
    explicit_other_church_schedule = [c for c in church_sorted_schedules
                                      if c.is_church_explicitly_other]
    if not explicit_other_church_schedule:
        return False

    return len(explicit_other_church_schedule[0].sorted_schedules) <= 1


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


################
# MERGE & SORT #
################

def get_merged_schedule_items(church_schedule_items: list[ChurchScheduleItem]
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


def church_schedule_item_sort_key(church_schedule_item: ChurchScheduleItem) -> tuple:
    return schedule_item_sort_key(church_schedule_item.schedule_item.item)


def get_sorted_schedules_by_church_id(church_schedules: list[ChurchScheduleItem]
                                      ) -> dict[int, list[ChurchScheduleItem]]:
    sorted_schedules_by_church_id = {}

    for church_schedule in sorted(church_schedules, key=church_schedule_item_sort_key):
        sorted_schedules_by_church_id.setdefault(church_schedule.schedule_item.item.church_id, [])\
            .append(church_schedule)

    return sorted_schedules_by_church_id
