from uuid import UUID

from front.public_service import front_get_church_color_by_uuid
from registry.models import Website
from scheduling.models import IndexEvent, Scheduling, Parsing
from scheduling.services.merging.holiday_zone_service import get_website_holiday_zone
from scheduling.services.merging.sourced_schedules_service import SchedulingElements
from scheduling.utils.date_utils import time_plus_hours
from scheduling.workflows.merging.sources import ParsingSource, BaseSource, OClocherSource
from scheduling.workflows.parsing.rrule_utils import get_events_from_schedule_item
from scheduling.workflows.parsing.schedules import Event


def source_has_been_moderated(source: BaseSource,
                              parsing_by_uuid: dict[UUID, Parsing]) -> bool:
    if isinstance(source, ParsingSource):
        return parsing_by_uuid[source.parsing_uuid].has_been_moderated()

    if isinstance(source, OClocherSource):
        return True

    raise NotImplementedError


def generate_unique_events_by_church_id(website: Website, scheduling_elements: SchedulingElements
                                        ) -> dict[int | None, list[tuple[Event, bool]]]:
    parsing_by_uuid = {parsing.uuid: parsing for parsing in scheduling_elements.parsings}
    holiday_zone = get_website_holiday_zone(website,
                                            list(scheduling_elements.church_by_id.values()))

    events_by_church_id = {}
    for sourced_schedules_of_church in \
            scheduling_elements.sourced_schedules_list.sourced_schedules_of_churches:
        if not sourced_schedules_of_church.is_real_church():
            # We do not create events if not real church
            continue

        has_been_moderated_by_church_event = {}
        for sourced_schedule_item in sourced_schedules_of_church.sourced_schedules:
            has_been_moderated = any(source_has_been_moderated(source, parsing_by_uuid)
                                     for source in sourced_schedule_item.sources)
            events = get_events_from_schedule_item(sourced_schedule_item.item, holiday_zone,
                                                   max_days=10)
            for event in events:
                has_been_moderated_by_church_event[event] = \
                    has_been_moderated or has_been_moderated_by_church_event.get(event, False)

        unique_events = []
        for event, has_been_moderated in has_been_moderated_by_church_event.items():
            unique_events.append((event, has_been_moderated))

        events_by_church_id[sourced_schedules_of_church.church_id] = unique_events

    return events_by_church_id


def build_index_events(scheduling: Scheduling,
                       scheduling_elements: SchedulingElements,
                       events_by_church_id: dict[int | None, list[tuple[Event, bool]]]
                       ) -> list[IndexEvent]:
    church_color_by_uuid = front_get_church_color_by_uuid(
        scheduling_elements.sourced_schedules_list,
        scheduling_elements.church_by_id
    )

    index_events = []
    for church_id, event_and_moderations in events_by_church_id.items():
        church = scheduling_elements.church_by_id[church_id]
        church_color = church_color_by_uuid[church.uuid]

        for event, has_been_moderated in event_and_moderations:
            event_day = event.start.date()
            event_start_time = event.start.time()
            displayed_end_time = event.end.time() if event.end else None
            indexed_end_time = displayed_end_time or time_plus_hours(event_start_time, 4)

            index_events.append(IndexEvent(
                scheduling=scheduling,
                church=church,
                day=event_day,
                start_time=event_start_time,
                indexed_end_time=indexed_end_time,
                displayed_end_time=displayed_end_time,
                has_been_moderated=has_been_moderated,
                church_color=church_color,
            ))

    return index_events


def build_sourced_schedules_and_index_events(website: Website, scheduling: Scheduling,
                                             scheduling_elements: SchedulingElements
                                             ) -> list[IndexEvent]:
    # Generate events by church_id
    events_by_church_id = generate_unique_events_by_church_id(website, scheduling_elements)

    # Build index events
    index_event = build_index_events(scheduling, scheduling_elements, events_by_church_id)

    return index_event
