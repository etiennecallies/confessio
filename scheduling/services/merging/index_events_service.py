from uuid import UUID

from front.services.card.church_color_service import get_color_of_nullable_church, \
    get_church_color_by_uuid
from front.services.card.holiday_zone_service import get_website_holiday_zone
from front.services.card.website_events_service import ChurchEvent
from registry.models import Website
from scheduling.models import IndexEvent, Scheduling, Parsing
from scheduling.services.merging.sourced_schedules_service import build_scheduling_elements
from scheduling.utils.date_utils import time_plus_hours
from scheduling.workflows.merging.sources import ParsingSource, BaseSource, OClocherSource
from scheduling.workflows.parsing.rrule_utils import get_events_from_schedule_item


def build_website_church_events(website: Website,
                                scheduling: Scheduling,
                                ) -> list[IndexEvent]:

    all_church_events = get_all_church_events(website, scheduling)

    start_end_with_churches = set()
    for church_event in all_church_events:
        if church_event.church:
            start_end_with_churches.add((church_event.start, church_event.end))

    website_churches = website.get_churches()
    church_index_to_add = []
    for church_event in all_church_events:
        event_day = church_event.start.date()
        event_start_time = church_event.start.time()
        displayed_end_time = church_event.end.time() if church_event.end else None
        indexed_end_time = displayed_end_time or time_plus_hours(event_start_time, 4)
        if church_event.church:
            church_index_to_add.append(IndexEvent(
                scheduling=scheduling,
                church=church_event.church,
                day=event_day,
                start_time=event_start_time,
                indexed_end_time=indexed_end_time,
                displayed_end_time=displayed_end_time,
                is_explicitely_other=None,
                has_been_moderated=church_event.has_been_moderated,
                church_color=church_event.church_color,
            ))
        else:
            if (church_event.start, church_event.end) in start_end_with_churches:
                # We ignore church_event with no church and with real-church event
                continue

            for church in website_churches:
                church_index_to_add.append(IndexEvent(
                    scheduling=scheduling,
                    church=church,
                    day=event_day,
                    start_time=event_start_time,
                    indexed_end_time=indexed_end_time,
                    displayed_end_time=displayed_end_time,
                    is_explicitely_other=church_event.is_church_explicitly_other,
                    has_been_moderated=church_event.has_been_moderated,
                    church_color=church_event.church_color,
                ))

    return church_index_to_add


def source_has_been_moderated(source: BaseSource,
                              parsing_by_uuid: dict[UUID, Parsing]) -> bool:
    if isinstance(source, ParsingSource):
        return parsing_by_uuid[source.parsing_uuid].has_been_moderated()

    if isinstance(source, OClocherSource):
        return True

    raise NotImplementedError


def get_all_church_events(website: Website, scheduling: Scheduling,
                          ) -> list[ChurchEvent]:
    all_church_events = []
    scheduling_elements = build_scheduling_elements(website, scheduling)
    parsing_by_uuid = {parsing.uuid: parsing for parsing in scheduling_elements.parsings}

    holiday_zone = get_website_holiday_zone(website,
                                            list(scheduling_elements.church_by_id.values()))
    church_color_by_uuid = get_church_color_by_uuid(scheduling_elements.sourced_schedules_list,
                                                    scheduling_elements.church_by_id)
    for sourced_schedules_of_church in \
            scheduling_elements.sourced_schedules_list.sourced_schedules_of_churches:
        church = scheduling_elements.church_by_id.get(sourced_schedules_of_church.church_id, None)

        has_been_moderated_by_church_event = {}
        for sourced_schedule_item in sourced_schedules_of_church.sourced_schedules:
            has_been_moderated = any(source_has_been_moderated(source, parsing_by_uuid)
                                     for source in sourced_schedule_item.sources)
            events = get_events_from_schedule_item(sourced_schedule_item.item, holiday_zone,
                                                   max_days=10)
            for event in events:
                has_been_moderated_by_church_event[event] = \
                    has_been_moderated or has_been_moderated_by_church_event.get(event, False)

        for event, has_been_moderated in has_been_moderated_by_church_event.items():
            church_event = ChurchEvent(
                church=church,
                is_church_explicitly_other=sourced_schedules_of_church.is_church_explicitly_other(),
                start=event.start,
                end=event.end,
                has_been_moderated=has_been_moderated,
                church_color=get_color_of_nullable_church(
                    church,
                    church_color_by_uuid,
                    sourced_schedules_of_church.is_church_explicitly_other()
                )
            )
            all_church_events.append(church_event)

    return all_church_events
