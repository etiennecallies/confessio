from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from home.models import Church, Website
from home.services.holiday_zone_service import get_website_holiday_zone
from home.services.sources_service import sort_parsings
from home.utils.date_utils import get_current_year
from home.utils.hash_utils import hash_string_to_hex
from home.utils.list_utils import get_desc_by_id
from scheduling.models import Scheduling
from scheduling.models.parsing_models import Parsing
from scheduling.services.scheduling_service import get_scheduling_sources
from scheduling.workflows.merging.merge_schedule_items import get_merged_sourced_schedule_items
from scheduling.workflows.merging.sort_schedule_items import \
    get_sorted_sourced_schedule_items_by_church_id
from scheduling.workflows.merging.sourced_schedule_items import SourcedScheduleItem
from scheduling.workflows.merging.sources import ParsingSource, BaseSource
from scraping.parse.explain_schedule import get_explanation_from_schedule
from scraping.parse.rrule_utils import get_events_from_schedule_item
from scraping.services.parsing_service import get_parsing_schedules_list, get_church_desc_by_id


#############
# SCHEDULES #
#############


@dataclass
class ChurchSortedSchedules:
    church: Optional[Church]
    is_church_explicitly_other: bool
    sourced_schedule_items: list[SourcedScheduleItem]

    @classmethod
    def from_sorted_schedules(cls, sourced_schedule_items: list[SourcedScheduleItem],
                              church_id: int | None,
                              church_by_id: dict[int, Church]) -> 'ChurchSortedSchedules':
        return cls(
            church=church_by_id[church_id] if church_id is not None and church_id != -1 else None,
            is_church_explicitly_other=church_id == -1,
            sourced_schedule_items=sourced_schedule_items,
        )


@dataclass
class WebsiteSchedules:
    church_sorted_schedules: list[ChurchSortedSchedules]
    possible_by_appointment_sources: list[BaseSource]
    is_related_to_mass_sources: list[BaseSource]
    is_related_to_adoration_sources: list[BaseSource]
    is_related_to_permanence_sources: list[BaseSource]
    will_be_seasonal_events_sources: list[BaseSource]
    parsing_index_by_parsing_uuid: dict[UUID, int]
    parsing_by_uuid: dict[UUID, Parsing]
    church_color_by_uuid: dict[UUID, str]


def get_website_schedules(website: Website,
                          website_churches: list[Church],
                          scheduling: Scheduling | None,
                          max_days: int = 1,
                          only_real_churches: bool = False,
                          ) -> WebsiteSchedules:
    ###############
    # Get sources #
    ###############

    scheduling_sources = get_scheduling_sources(scheduling)

    church_by_desc = {church.get_desc(): church for church in scheduling_sources.churches}
    church_desc_by_id = get_desc_by_id(list(church_by_desc.keys()))
    church_by_id = {church_id: church_by_desc[desc]
                    for church_id, desc in church_desc_by_id.items()}

    sources = []
    for parsing in scheduling_sources.parsings:
        assert get_church_desc_by_id(parsing) == church_desc_by_id
        sources.append(ParsingSource(
            schedules_list=get_parsing_schedules_list(parsing),
            parsing_uuid=parsing.uuid,
        ))

    ###########################
    # Get SourcedScheduleItem #
    ###########################

    all_sourced_schedule_items = []

    start_date = date.today()
    current_year = get_current_year()
    end_date = start_date + timedelta(days=300)

    holiday_zone = get_website_holiday_zone(website, website_churches)
    website_church_uuids = set(c.uuid for c in website_churches)

    possible_by_appointment_sources = []
    is_related_to_mass_sources = []
    is_related_to_adoration_sources = []
    is_related_to_permanence_sources = []
    will_be_seasonal_events_sources = []

    for source in sources:
        schedules_list = source.schedules_list
        if schedules_list is None:
            continue

        for schedule_item in schedules_list.schedules:
            if schedule_item.has_real_church() and \
                    church_by_id[schedule_item.church_id].uuid not in website_church_uuids:
                # can happen when we seek for schedules for a specific church
                continue

            if only_real_churches and not schedule_item.has_real_church():
                continue

            events = get_events_from_schedule_item(schedule_item, start_date,
                                                   current_year, holiday_zone,
                                                   end_date, max_days=max_days)
            if events:
                all_sourced_schedule_items.append(
                    SourcedScheduleItem(
                        item=schedule_item,
                        explanation=get_explanation_from_schedule(schedule_item),
                        sources=[source],
                        events=events,
                    )
                )

        if schedules_list.possible_by_appointment:
            possible_by_appointment_sources.append(source)
        if schedules_list.is_related_to_mass:
            is_related_to_mass_sources.append(source)
        if schedules_list.is_related_to_adoration:
            is_related_to_adoration_sources.append(source)
        if schedules_list.is_related_to_permanence:
            is_related_to_permanence_sources.append(source)
        if schedules_list.will_be_seasonal_events:
            will_be_seasonal_events_sources.append(source)

    merged_sourced_schedule_items = get_merged_sourced_schedule_items(all_sourced_schedule_items)
    sorted_sourced_schedule_items_by_church_id = get_sorted_sourced_schedule_items_by_church_id(
        merged_sourced_schedule_items
    )

    #############################
    # Get ChurchSortedSchedules #
    #############################

    church_sorted_schedules = [
        ChurchSortedSchedules.from_sorted_schedules(sourced_schedule_items, church_id, church_by_id)
        for church_id, sourced_schedule_items in sorted_sourced_schedule_items_by_church_id.items()
    ]

    # Add churches without events
    churches_with_events = {church_by_id.get(sourced_schedule_item.item.church_id, None)
                            for sourced_schedule_item in merged_sourced_schedule_items}
    churches_with_events_uuids = {c.uuid for c in churches_with_events if c is not None}
    church_sorted_schedules += [
        ChurchSortedSchedules(
            church=c,
            is_church_explicitly_other=False,
            sourced_schedule_items=[]
        ) for c in website_churches if c.uuid not in churches_with_events_uuids
    ]

    parsing_index_by_parsing_uuid = {
        parsing.uuid: i for i, parsing in enumerate(sort_parsings(scheduling_sources.parsings))
    }
    parsing_by_uuid = {parsing.uuid: parsing for parsing in scheduling_sources. parsings}

    return WebsiteSchedules(
        church_sorted_schedules=church_sorted_schedules,
        possible_by_appointment_sources=possible_by_appointment_sources,
        is_related_to_mass_sources=is_related_to_mass_sources,
        is_related_to_adoration_sources=is_related_to_adoration_sources,
        is_related_to_permanence_sources=is_related_to_permanence_sources,
        will_be_seasonal_events_sources=will_be_seasonal_events_sources,
        parsing_index_by_parsing_uuid=parsing_index_by_parsing_uuid,
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
