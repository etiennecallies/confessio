from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

from home.models import Church, Parsing, Website, Page, Pruning
from home.utils.date_utils import get_current_year
from home.utils.hash_utils import hash_string_to_hex
from scraping.parse.explain_schedule import schedule_item_sort_key, get_explanation_from_schedule
from scraping.parse.rrule_utils import get_events_from_schedule_item
from scraping.parse.schedules import Event, ScheduleItem
from scraping.services.parse_pruning_service import get_parsing_schedules_list, get_church_by_id, \
    has_schedules


#########################
# PARSINGS AND PRUNINGS #
#########################

@dataclass
class WebsiteParsingsAndPrunings:
    sources: list[Parsing]
    source_index_by_parsing_uuid: dict[UUID, int]
    page_by_parsing_uuid: dict[UUID, Page]
    all_pages_by_parsing_uuid: dict[UUID, list[Page]]
    prunings_by_parsing_uuid: dict[UUID, list[Pruning]]
    page_scraping_last_created_at_by_parsing_uuid: dict[UUID, Optional[datetime]]
    parsings_have_been_moderated: bool


def get_website_parsings_and_prunings(website: Website) -> WebsiteParsingsAndPrunings:
    sources = []
    source_index_by_parsing_uuid = {}
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

            if parsing.uuid not in source_index_by_parsing_uuid:
                source_index_by_parsing_uuid[parsing.uuid] = len(sources)
                sources.append(parsing)

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
        sources=sources,
        source_index_by_parsing_uuid=source_index_by_parsing_uuid,
        page_by_parsing_uuid=page_by_parsing_uuid,
        all_pages_by_parsing_uuid=all_pages_by_parsing_uuid,
        prunings_by_parsing_uuid=prunings_by_parsing_uuid,
        page_scraping_last_created_at_by_parsing_uuid=page_scraping_last_created_at_by_parsing_uuid,
        parsings_have_been_moderated=all(parsing.has_been_moderated() for parsing in sources)
    )


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
    parsings_and_prunings: WebsiteParsingsAndPrunings

    def next_event_in_church(self, church: Church) -> Optional[Event]:
        for church_events in self.church_events_by_day.values():
            for church_event in church_events:
                if church_event.church == church:
                    return church_event.event

        return None


def get_merged_church_schedules_list(website: Website,
                                     all_website_churches: list[Church],
                                     day_filter: date | None = None
                                     ) -> MergedChurchSchedulesList | None:
    ################
    # Get parsings #
    ################
    parsings_and_prunings = get_website_parsings_and_prunings(website)

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
        max_days = 8
    else:
        start_date = day_filter
        current_year = start_date.year
        end_date = start_date
        max_days = 1

    for parsing in parsings_and_prunings.sources:
        church_by_id = get_church_by_id(parsing, website)

        schedules_list = get_parsing_schedules_list(parsing)
        if schedules_list is None:
            continue

        for schedule in schedules_list.schedules:
            events = get_events_from_schedule_item(schedule, start_date,
                                                   current_year, end_date, max_days=max_days)
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

    if day_filter:
        if not all_church_schedule_items:
            # If we are filtering on a specific day and no events are found, we return None
            return None

    merged_church_schedule_items = get_merged_schedule_items(all_church_schedule_items)
    # TODO we shall make sure the church_id are the same accross all parsings
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

    return MergedChurchSchedulesList(
        church_events_by_day=church_events_by_day,
        church_sorted_schedules=church_sorted_schedules,
        possible_by_appointment_parsings=possible_by_appointment_parsings,
        is_related_to_mass_parsings=is_related_to_mass_parsings,
        is_related_to_adoration_parsings=is_related_to_adoration_parsings,
        is_related_to_permanence_parsings=is_related_to_permanence_parsings,
        will_be_seasonal_events_parsings=will_be_seasonal_events_parsings,
        parsings_and_prunings=parsings_and_prunings
    )


def get_merged_church_schedules_list_for_website(website: Website,
                                                 website_churches: list[Church],
                                                 day_filter: date | None = None
                                                 ) -> MergedChurchSchedulesList | None:
    if not website.all_pages_parsed() or website.unreliability_reason:
        return None

    return get_merged_church_schedules_list(website, website_churches, day_filter)


def get_website_merged_church_schedules_list(websites: list[Website],
                                             website_churches: dict[UUID, list[Church]],
                                             day_filter: date | None = None
                                             ) -> dict[UUID, MergedChurchSchedulesList]:
    website_merged_church_schedules_list = {}
    for website in websites:
        merged_church_schedules_list = get_merged_church_schedules_list_for_website(
            website, website_churches[website.uuid], day_filter)
        if merged_church_schedules_list:
            website_merged_church_schedules_list[website.uuid] = merged_church_schedules_list

    return website_merged_church_schedules_list


##########
# COLORS #
##########

def get_church_color(church: Church | None, is_church_explicitly_other: bool) -> str:
    if is_church_explicitly_other:
        return '#A91E2C'

    if church is None:
        return 'lightgray'

    # Generate a hash of the string
    hash_hex = hash_string_to_hex(str(church.uuid))

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


################
# MERGE & SORT #
################

def get_merged_schedule_items(church_schedule_items: list[ChurchScheduleItem]
                              ) -> list[ChurchScheduleItem]:
    schedules_by_explanation_and_item = {}
    for church_schedule_item in church_schedule_items:
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
