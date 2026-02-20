from uuid import UUID

from front.services.card.church_color_service import get_color_of_nullable_church, \
    get_church_color_by_uuid
from front.services.card.holiday_zone_service import get_website_holiday_zone
from registry.models import Website
from scheduling.models import IndexEvent, Scheduling, Parsing
from scheduling.services.merging.sourced_schedules_service import build_scheduling_elements, \
    SchedulingElements
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


def keep_only_real_church_events(events_by_church_id: dict[int | None, list[tuple[Event, bool]]]
                                 ) -> dict[int, list[tuple[Event, bool]]]:
    start_end_with_churches = set()
    for church_id, event_and_moderations in events_by_church_id.items():
        if church_id is None or church_id == -1:
            continue

        for event, has_been_moderated in event_and_moderations:
            start_end_with_churches.add((event.start, event.end))

    new_events_by_church_id = {}
    for church_id, event_and_moderations in events_by_church_id.items():
        if church_id is None or church_id == -1:
            new_event_and_moderations = []
            for event, has_been_moderated in event_and_moderations:
                if (event.start, event.end) in start_end_with_churches:
                    # We ignore event with no church having similar real-church event
                    continue

                new_event_and_moderations.append((event, has_been_moderated))
            new_events_by_church_id[church_id] = new_event_and_moderations
        else:
            new_events_by_church_id[church_id] = event_and_moderations

    return new_events_by_church_id


def build_index_events(scheduling: Scheduling,
                       scheduling_elements: SchedulingElements,
                       events_by_church_id: dict[int | None, list[tuple[Event, bool]]]
                       ) -> list[IndexEvent]:
    church_color_by_uuid = get_church_color_by_uuid(scheduling_elements.sourced_schedules_list,
                                                    scheduling_elements.church_by_id)

    index_events = []
    for church_id, event_and_moderations in events_by_church_id.items():
        church = scheduling_elements.church_by_id.get(church_id, None)
        is_explicitely_other = church_id == -1
        church_color = get_color_of_nullable_church(church, church_color_by_uuid,
                                                    is_explicitely_other)

        for event, has_been_moderated in event_and_moderations:
            event_day = event.start.date()
            event_start_time = event.start.time()
            displayed_end_time = event.end.time() if event.end else None
            indexed_end_time = displayed_end_time or time_plus_hours(event_start_time, 4)

            if church:
                index_events.append(IndexEvent(
                    scheduling=scheduling,
                    church=church,
                    day=event_day,
                    start_time=event_start_time,
                    indexed_end_time=indexed_end_time,
                    displayed_end_time=displayed_end_time,
                    is_explicitely_other=is_explicitely_other,
                    has_been_moderated=has_been_moderated,
                    church_color=church_color,
                ))
            else:
                for website_church in scheduling_elements.church_by_id.values():
                    index_events.append(IndexEvent(
                        scheduling=scheduling,
                        church=website_church,
                        day=event_day,
                        start_time=event_start_time,
                        indexed_end_time=indexed_end_time,
                        displayed_end_time=displayed_end_time,
                        is_explicitely_other=is_explicitely_other,
                        has_been_moderated=has_been_moderated,
                        church_color=church_color,
                    ))

    return index_events


def build_sourced_schedules_and_index_events(website: Website, scheduling: Scheduling,
                                             ) -> list[IndexEvent]:
    # Build scheduling elements
    scheduling_elements = build_scheduling_elements(website, scheduling)

    # Generate events by church_id
    events_by_church_id = generate_unique_events_by_church_id(website, scheduling_elements)

    # Keep only real-church events or not-seen events
    events_by_church_id = keep_only_real_church_events(events_by_church_id)

    # Build index events
    return build_index_events(scheduling, scheduling_elements, events_by_church_id)
