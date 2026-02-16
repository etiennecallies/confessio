from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from fetching.services.oclocher_matching_service import get_matching_church_desc_by_id, \
    get_location_desc_by_id, get_matching_location_desc_by_id, get_location_desc
from front.services.card.holiday_zone_service import get_website_holiday_zone
from front.services.card.sources_service import sort_parsings
from front.services.card.timezone_service import get_timezone_of_churches
from registry.models import Church, Website
from scheduling.models import Parsing
from scheduling.models import Scheduling
from scheduling.services.merging.oclocher_schedules_services import \
    get_schedules_list_from_oclocher_schedules
from scheduling.services.parsing.parsing_service import get_parsing_schedules_list, \
    get_parsing_church_desc_by_id
from scheduling.services.scheduling.scheduling_service import get_scheduling_sources, \
    SchedulingSources
from scheduling.utils.date_utils import get_current_year
from scheduling.utils.hash_utils import hash_string_to_hex
from scheduling.utils.list_utils import get_desc_by_id
from scheduling.workflows.merging.merge_schedule_items import get_merged_sourced_schedule_items
from scheduling.workflows.merging.sort_schedule_items import \
    get_sorted_sourced_schedule_items_by_church_id
from scheduling.workflows.merging.sourced_schedules import SourcedScheduleItem, \
    SourcedSchedulesList, SourcedSchedulesOfChurch
from scheduling.workflows.merging.sources import ParsingSource, BaseSource, OClocherSource
from scheduling.workflows.parsing.explain_schedule import get_explanation_from_schedule
from scheduling.workflows.parsing.rrule_utils import get_events_from_schedule_item

MAX_SCHEDULES_PER_CHURCH = 30


@dataclass
class WebsiteSchedules:
    sourced_schedules_list: SourcedSchedulesList
    church_by_id: dict[int, Church]
    parsing_index_by_parsing_uuid: dict[UUID, int]
    parsing_by_uuid: dict[UUID, Parsing]
    church_color_by_uuid: dict[UUID, str]


def get_website_schedules(website: Website,
                          website_churches: list[Church],
                          scheduling: Scheduling | None,
                          max_days: int = 1,
                          only_real_churches: bool = False,
                          ) -> WebsiteSchedules:
    scheduling_sources = get_scheduling_sources(scheduling)
    church_by_id, sources = get_church_by_id_and_sources(scheduling_sources)

    sourced_schedules_list = get_sourced_schedules_list(
        website, website_churches, church_by_id, sources, max_days, only_real_churches
    )

    parsing_index_by_parsing_uuid = {
        parsing.uuid: i for i, parsing in enumerate(sort_parsings(scheduling_sources.parsings))
    }
    parsing_by_uuid = {parsing.uuid: parsing for parsing in scheduling_sources.parsings}

    return WebsiteSchedules(
        sourced_schedules_list=sourced_schedules_list,
        church_by_id=church_by_id,
        parsing_index_by_parsing_uuid=parsing_index_by_parsing_uuid,
        parsing_by_uuid=parsing_by_uuid,
        church_color_by_uuid=get_church_color_by_uuid(sourced_schedules_list, church_by_id),
    )


############################
# CHURCH BY ID AND SOURCES #
############################

def get_church_by_id_and_sources(scheduling_sources: SchedulingSources,
                                 ) -> tuple[dict[int, Church], list[BaseSource]]:
    church_by_desc = {church.get_desc(): church for church in scheduling_sources.churches}
    church_desc_by_id = get_desc_by_id(list(church_by_desc.keys()))
    church_by_id = {church_id: church_by_desc[desc]
                    for church_id, desc in church_desc_by_id.items()}

    sources = []
    for parsing in scheduling_sources.parsings:
        assert get_parsing_church_desc_by_id(parsing) == church_desc_by_id, \
            f'Parsing churches: {get_parsing_church_desc_by_id(parsing)}' \
            f'Scheduling churches: {church_desc_by_id}'
        sources.append(ParsingSource(
            schedules_list=get_parsing_schedules_list(parsing),
            parsing_uuid=parsing.uuid,
        ))

    if scheduling_sources.oclocher_schedules:
        oclocher_matching = scheduling_sources.oclocher_matching
        assert oclocher_matching is not None
        assert get_matching_church_desc_by_id(oclocher_matching) == church_desc_by_id

        location_desc_by_id = get_location_desc_by_id(scheduling_sources.oclocher_locations)
        assert get_matching_location_desc_by_id(oclocher_matching) == location_desc_by_id
        location_by_desc = {get_location_desc(location): location
                            for location in scheduling_sources.oclocher_locations}
        oclocher_id_by_location_id = {location_id: location_by_desc[desc].location_id
                                      for location_id, desc in location_desc_by_id.items()}

        timezone_str = get_timezone_of_churches(scheduling_sources.churches)

        schedules_list = get_schedules_list_from_oclocher_schedules(
            scheduling_sources.oclocher_schedules,
            oclocher_matching,
            oclocher_id_by_location_id,
            timezone_str,
        )
        sources.append(OClocherSource(schedules_list=schedules_list))

    return church_by_id, sources


########################
# SourcedSchedulesList #
########################

def get_sourced_schedules_list(website: Website,
                               website_churches: list[Church],
                               church_by_id: dict[int, Church],
                               sources: list[BaseSource],
                               max_days: int,
                               only_real_churches: bool,
                               ) -> SourcedSchedulesList:
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

    #####################################
    # Get sourced_schedules_of_churches #
    #####################################

    sourced_schedules_of_churches = [
        SourcedSchedulesOfChurch(
            church_id=church_id,
            sourced_schedules=sourced_schedule_items[:MAX_SCHEDULES_PER_CHURCH],
        )
        for church_id, sourced_schedule_items in sorted_sourced_schedule_items_by_church_id.items()
    ]

    # Add churches without events
    church_ids_with_events = {ssc.church_id for ssc in sourced_schedules_of_churches}
    sourced_schedules_of_churches += [
        SourcedSchedulesOfChurch(
            church_id=church_id,
            sourced_schedules=[]
        ) for church_id in church_by_id if church_id not in church_ids_with_events
    ]

    return SourcedSchedulesList(
        sourced_schedules_of_churches=sourced_schedules_of_churches,
        possible_by_appointment_sources=possible_by_appointment_sources,
        is_related_to_mass_sources=is_related_to_mass_sources,
        is_related_to_adoration_sources=is_related_to_adoration_sources,
        is_related_to_permanence_sources=is_related_to_permanence_sources,
        will_be_seasonal_events_sources=will_be_seasonal_events_sources,
    )


##########
# COLORS #
##########

def get_church_color_by_uuid(sourced_schedules_list: SourcedSchedulesList,
                             church_by_id: dict[int, Church]) -> dict[UUID, str]:
    church_color_by_uuid = {}
    index = 0
    for sourced_schedules_of_church in sourced_schedules_list.sourced_schedules_of_churches:
        church = church_by_id.get(sourced_schedules_of_church.church_id, None)
        if church:
            church_color_by_uuid[church.uuid] = get_church_color(index)
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
