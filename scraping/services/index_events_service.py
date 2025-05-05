from home.models import Website, ChurchIndexEvent, Church
from home.services.website_events_service import ChurchEvent
from home.services.website_schedules_service import get_website_schedules, \
    get_color_of_nullable_church
from home.utils.date_utils import time_plus_hours


def index_events_for_website(website: Website):
    website_churches = []
    for parish in website.parishes.all():
        for church in parish.churches.all():
            website_churches.append(church)

    all_church_events = []
    if not website.unreliability_reason:
        all_church_events = get_all_church_events(website, website_churches)

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
            church_index_to_add.append(ChurchIndexEvent(
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
                church_index_to_add.append(ChurchIndexEvent(
                    church=church,
                    day=event_day,
                    start_time=event_start_time,
                    indexed_end_time=indexed_end_time,
                    displayed_end_time=displayed_end_time,
                    is_explicitely_other=church_event.is_church_explicitly_other,
                    has_been_moderated=church_event.has_been_moderated,
                    church_color=church_event.church_color,
                ))

    # Remove existing events
    ChurchIndexEvent.objects.filter(church__in=website_churches).delete()

    for website_index_event in church_index_to_add:
        website_index_event.save()


def get_all_church_events(website: Website, website_churches: list[Church]
                          ) -> list[ChurchEvent]:
    all_church_events = []
    website_schedules = get_website_schedules(
        website, website_churches, day_filter=None, max_days=10
    )
    for church_sorted_schedule in website_schedules.church_sorted_schedules:
        has_been_moderated_by_church_event = {}
        for sorted_schedule in church_sorted_schedule.sorted_schedules:
            parsings = [website_schedules.parsing_by_uuid[parsing_uuid]
                        for parsing_uuid in sorted_schedule.parsing_uuids]
            has_been_moderated = any(p.has_been_moderated() for p in parsings)
            for event in sorted_schedule.events:
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
