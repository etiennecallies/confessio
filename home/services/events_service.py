from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from home.models import Church, Parsing, Website, Page, Pruning
from home.utils.date_utils import get_current_year, get_end_of_next_two_weeks, datetime_to_date
from home.utils.hash_utils import hash_string_to_hex
from scraping.parse.explain_schedule import schedule_item_sort_key
from scraping.parse.rrule_utils import get_events_from_schedule_items
from scraping.parse.schedules import Event, ScheduleItem, SchedulesList, get_merged_schedules_list
from scraping.services.parse_pruning_service import get_parsing_schedules_list, get_church_by_id, \
    has_schedules


@dataclass
class ParsingScheduleItem:
    item: ScheduleItem
    parsing: Parsing


@dataclass
class ChurchScheduleItem:
    church: Optional[Church]
    is_church_explicitly_other: bool
    schedule_item: ParsingScheduleItem

    @classmethod
    def from_schedule_item(cls, schedule_item: ScheduleItem, parsing: Parsing,
                           church_by_id: dict[int, Church]) -> 'ChurchScheduleItem':
        parsing_schedule_item = ParsingScheduleItem(schedule_item, parsing)
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
class ChurchSchedulesList:
    church_schedules: list[ChurchScheduleItem]
    schedules_list: SchedulesList

    @classmethod
    def from_parsing(cls, parsing: Parsing, website: Website) -> Optional['ChurchSchedulesList']:
        schedules_list = get_parsing_schedules_list(parsing)
        if schedules_list is None:
            return None

        church_by_id = get_church_by_id(parsing, website)
        church_schedules = [ChurchScheduleItem.from_schedule_item(schedule, parsing, church_by_id)
                            for schedule in schedules_list.schedules]

        return cls(
            church_schedules=church_schedules,
            schedules_list=schedules_list
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

    church_by_id = {cs.schedule_item.item.church_id: cs.church for cs in church_schedules}
    church_events = [ChurchEvent.from_event(event, church_by_id) for event in events]

    church_schedule_items = get_sorted_schedules_by_church_id(church_schedules)
    church_sorted_schedules = [
        ChurchSortedSchedules.from_sorted_schedules(church_schedules, church_id, church_by_id)
        for church_id, church_schedules in church_schedule_items.items()
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


#########################
# PARSINGS AND PRUNINGS #
#########################

@dataclass
class WebsiteParsingsAndPrunings:
    parsings_by_uuid: dict[UUID, Parsing]
    page_by_parsing_uuid: dict[UUID, Page]
    all_pages_by_parsing_uuid: dict[UUID, list[Page]]
    prunings_by_parsing_uuid: dict[UUID, list[Pruning]]
    page_scraping_last_created_at_by_parsing_uuid: dict[UUID, Optional[datetime]]


def get_website_parsings_and_prunings(website: Website) -> WebsiteParsingsAndPrunings:
    parsings_by_uuid = {}
    page_by_parsing_uuid = {}
    all_pages_by_parsing_uuid = {}
    prunings_by_parsing_uuid = {}
    page_scraping_last_created_at_by_parsing_uuid = {}
    for page in website.get_pages():
        if page.scraping is None:
            continue

        for pruning in page.get_prunings():
            parsing = page.get_parsing(pruning)
            if parsing is None or not has_schedules(parsing):
                continue

            parsings_by_uuid[parsing.uuid] = parsing

            page_scraping_last_created_at = page_scraping_last_created_at_by_parsing_uuid.get(
                parsing.uuid, None)
            if page_scraping_last_created_at is None \
                    or page.scraping.created_at > page_scraping_last_created_at:
                page_scraping_last_created_at_by_parsing_uuid[parsing.uuid] = \
                    page.scraping.created_at
                page_by_parsing_uuid[parsing.uuid] = page

            all_pages_by_parsing_uuid.setdefault(parsing.uuid, []).append(page)
            prunings_by_parsing_uuid.setdefault(parsing.uuid, []).append(pruning)

    return WebsiteParsingsAndPrunings(
        parsings_by_uuid=parsings_by_uuid,
        page_by_parsing_uuid=page_by_parsing_uuid,
        all_pages_by_parsing_uuid=all_pages_by_parsing_uuid,
        prunings_by_parsing_uuid=prunings_by_parsing_uuid,
        page_scraping_last_created_at_by_parsing_uuid=page_scraping_last_created_at_by_parsing_uuid
    )


def get_websites_parsings_and_prunings(websites: list[Website]
                                       ) -> dict[UUID, WebsiteParsingsAndPrunings]:
    websites_parsings_and_prunings = {}
    for website in websites:
        parsings_and_prunings = get_website_parsings_and_prunings(website)
        if parsings_and_prunings:
            websites_parsings_and_prunings[website.uuid] = parsings_and_prunings

    return websites_parsings_and_prunings


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


###########
# SORTING #
###########

def church_schedule_item_sort_key(church_schedule_item: ChurchScheduleItem) -> tuple:
    return schedule_item_sort_key(church_schedule_item.schedule_item.item)


def get_sorted_church_schedules(church_schedule_items: list[ChurchScheduleItem]
                                ) -> list[ChurchScheduleItem]:
    church_schedules_by_schedules = {}
    for church_schedule_item in church_schedule_items:
        church_schedules_by_schedules[church_schedule_item.schedule_item.item] = \
            church_schedule_item

    return sorted(list(church_schedules_by_schedules.values()), key=church_schedule_item_sort_key)


def get_sorted_schedules_by_church_id(church_schedules: list[ChurchScheduleItem]
                                      ) -> dict[int, list[ChurchScheduleItem]]:
    sorted_schedules_by_church_id = {}

    for church_schedule in get_sorted_church_schedules(church_schedules):
        sorted_schedules_by_church_id.setdefault(church_schedule.schedule_item.item.church_id, [])\
            .append(church_schedule)

    return sorted_schedules_by_church_id
