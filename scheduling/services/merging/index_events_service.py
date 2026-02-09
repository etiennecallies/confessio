from registry.models import Website, Church
from front.services.card.website_events_service import ChurchEvent
from front.services.card.website_schedules_service import get_website_schedules, \
    get_color_of_nullable_church, WebsiteSchedules
from scheduling.utils.date_utils import time_plus_hours
from scheduling.models import IndexEvent, Scheduling
from scheduling.workflows.merging.sources import ParsingSource, BaseSource, OClocherSource


def build_website_church_events(website: Website,
                                scheduling: Scheduling,
                                ) -> list[IndexEvent]:
    website_churches = website.get_churches()

    all_church_events = get_all_church_events(website, website_churches, scheduling)

    start_end_with_churches = set()
    for church_event in all_church_events:
        if church_event.church:
            start_end_with_churches.add((church_event.start, church_event.end))

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
                              website_schedules: WebsiteSchedules) -> bool:
    if isinstance(source, ParsingSource):
        return website_schedules.parsing_by_uuid[source.parsing_uuid].has_been_moderated()

    if isinstance(source, OClocherSource):
        return True

    raise NotImplementedError


def get_all_church_events(website: Website, website_churches: list[Church],
                          scheduling: Scheduling,
                          ) -> list[ChurchEvent]:
    all_church_events = []
    website_schedules = get_website_schedules(
        website, website_churches, scheduling, max_days=10
    )
    for church_sorted_schedule in website_schedules.church_sorted_schedules:
        has_been_moderated_by_church_event = {}
        for sourced_schedule_item in church_sorted_schedule.sourced_schedule_items:
            has_been_moderated = any(source_has_been_moderated(source, website_schedules)
                                     for source in sourced_schedule_item.sources)
            for event in sourced_schedule_item.events:
                has_been_moderated_by_church_event[event] = \
                    has_been_moderated or has_been_moderated_by_church_event.get(event, False)

        for event, has_been_moderated in has_been_moderated_by_church_event.items():
            church_event = ChurchEvent(
                church=church_sorted_schedule.church,
                is_church_explicitly_other=church_sorted_schedule.is_church_explicitly_other,
                start=event.start,
                end=event.end,
                has_been_moderated=has_been_moderated,
                church_color=get_color_of_nullable_church(
                    church_sorted_schedule.church,
                    website_schedules.church_color_by_uuid,
                    church_sorted_schedule.is_church_explicitly_other
                )
            )
            all_church_events.append(church_event)

    return all_church_events
