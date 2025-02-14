from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import UUID

from home.models import Church, Parsing, Website
from home.utils.date_utils import get_current_year, get_end_of_next_two_weeks, datetime_to_date
from home.utils.hash_utils import hash_string_to_hex
from scraping.parse.explain_schedule import get_sorted_schedules_by_church_id
from scraping.parse.rrule_utils import get_events_from_schedule_items
from scraping.parse.schedules import Event, ScheduleItem, SchedulesList, get_merged_schedules_list
from scraping.services.parse_pruning_service import get_parsing_schedules_list, get_church_by_id


@dataclass
class ChurchScheduleItem:
    church: Optional[Church]
    is_church_explicitly_other: bool
    schedule_item: ScheduleItem

    @classmethod
    def from_schedule_item(cls, schedule_item: ScheduleItem,
                           church_by_id: dict[int, Church]) -> 'ChurchScheduleItem':
        if schedule_item.church_id is None or schedule_item.church_id == -1:
            return cls(
                church=None,
                is_church_explicitly_other=schedule_item.church_id == -1,
                schedule_item=schedule_item,
            )

        return cls(
            church=church_by_id[schedule_item.church_id],
            is_church_explicitly_other=False,
            schedule_item=schedule_item,
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
class ChurchSchedulesList:
    church_schedules: list[ChurchScheduleItem]
    schedules_list: SchedulesList

    @classmethod
    def from_parsing(cls, parsing: Parsing, website: Website) -> Optional['ChurchSchedulesList']:
        schedules_list = get_parsing_schedules_list(parsing)
        if schedules_list is None:
            return None

        church_by_id = get_church_by_id(parsing, website)
        church_schedules = [ChurchScheduleItem.from_schedule_item(schedule, church_by_id)
                            for schedule in schedules_list.schedules]

        return cls(
            church_schedules=church_schedules,
            schedules_list=schedules_list
        )


@dataclass
class ChurchSortedSchedules:
    church: Optional[Church]
    is_church_explicitly_other: bool
    sorted_schedules: list[ScheduleItem]

    @classmethod
    def from_sorted_schedules(cls, sorted_schedules: list[ScheduleItem],
                              church_id: int | None,
                              church_by_id: dict[int, Church]) -> 'ChurchSortedSchedules':
        return cls(
            church=church_by_id[church_id] if church_id is not None and church_id != -1 else None,
            is_church_explicitly_other=church_id == -1,
            sorted_schedules=sorted_schedules,
        )


@dataclass
class MergedChurchSchedulesList:
    schedules_list: SchedulesList
    church_events: list[ChurchEvent]
    church_sorted_schedules: list[ChurchSortedSchedules]

    def next_event_in_church(self, church: Church) -> Optional[Event]:
        for church_event in self.church_events:
            if church_event.church == church:
                return church_event.event

        return None


def get_merged_church_schedules_list(csl: list[ChurchSchedulesList]
                                     ) -> MergedChurchSchedulesList:
    church_schedules = [cs for sl in csl for cs in sl.church_schedules]
    schedules_list = get_merged_schedules_list([cs.schedules_list for cs in csl])

    start_date = date.today()
    end_date = get_end_of_next_two_weeks()
    events = get_events_from_schedule_items(schedules_list.schedules, start_date, end_date,
                                            get_current_year(), max_events=None)

    church_by_id = {cs.schedule_item.church_id: cs.church for cs in church_schedules}
    church_events = [ChurchEvent.from_event(event, church_by_id) for event in events]

    sorted_schedules_by_church_id = get_sorted_schedules_by_church_id(schedules_list.schedules)
    church_sorted_schedules = [
        ChurchSortedSchedules.from_sorted_schedules(sorted_schedules, church_id, church_by_id)
        for church_id, sorted_schedules in sorted_schedules_by_church_id.items()
    ]

    return MergedChurchSchedulesList(
        schedules_list=schedules_list,
        church_events=church_events,
        church_sorted_schedules=church_sorted_schedules
    )


def get_merged_church_schedules_list_for_website(website: Website
                                                 ) -> MergedChurchSchedulesList | None:
    if not website.all_pages_parsed() or website.unreliability_reason:
        return

    church_schedules_lists = [ChurchSchedulesList.from_parsing(parsing, website)
                              for parsing in website.get_all_parsings()]
    return get_merged_church_schedules_list(
        [csl for csl in church_schedules_lists if csl is not None])


def get_website_merged_church_schedules_list(websites: list[Website]
                                             ) -> dict[UUID, MergedChurchSchedulesList]:
    website_merged_church_schedules_list = {}
    for website in websites:
        merged_church_schedules_list = get_merged_church_schedules_list_for_website(website)
        if merged_church_schedules_list:
            website_merged_church_schedules_list[website.uuid] = merged_church_schedules_list

    return website_merged_church_schedules_list


################
# EVENT BY DAY #
################

def get_church_events_by_day_by_website(
        website_merged_church_schedules_list: dict[UUID, MergedChurchSchedulesList]
) -> dict[UUID, dict[date, list[ChurchEvent]]]:
    church_events_by_day_by_website = {}
    for website_uuid, merged_church_schedules_list in website_merged_church_schedules_list.items():
        church_events_by_day = {}
        for church_event in merged_church_schedules_list.church_events:
            day = datetime_to_date(church_event.event.start)
            church_events_by_day.setdefault(day, []).append(church_event)
        church_events_by_day_by_website[website_uuid] = church_events_by_day

    return church_events_by_day_by_website


##########
# COLORS #
##########

def get_church_event_color(church: Church, start: str, end: str | None) -> str:
    # Create a unique string from the inputs
    unique_string = f"{church.name if church else ''}:{start}:{end or ''}"

    # Generate a hash of the string
    hash_hex = hash_string_to_hex(unique_string)

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
