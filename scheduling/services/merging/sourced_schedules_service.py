from datetime import date, timedelta

from front.services.card.holiday_zone_service import get_website_holiday_zone
from registry.models import Church, Website
from scheduling.public_model import SourcedSchedulesList
from scheduling.utils.date_utils import get_current_year
from scheduling.workflows.merging.merge_schedule_items import get_merged_sourced_schedule_items
from scheduling.workflows.merging.sort_schedule_items import \
    get_sorted_sourced_schedule_items_by_church_id
from scheduling.workflows.merging.sourced_schedules import SourcedScheduleItem, \
    SourcedSchedulesOfChurch
from scheduling.workflows.merging.sources import BaseSource
from scheduling.workflows.parsing.explain_schedule import get_explanation_from_schedule
from scheduling.workflows.parsing.rrule_utils import get_events_from_schedule_item


MAX_SCHEDULES_PER_CHURCH = 30


def get_sourced_schedules_list(website: Website,
                               church_by_id: dict[int, Church],
                               sources: list[BaseSource],
                               max_days: int,
                               ) -> SourcedSchedulesList:
    ###########################
    # Get SourcedScheduleItem #
    ###########################

    all_sourced_schedule_items = []

    start_date = date.today()
    current_year = get_current_year()
    end_date = start_date + timedelta(days=300)

    holiday_zone = get_website_holiday_zone(website, list(church_by_id.values()))

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
