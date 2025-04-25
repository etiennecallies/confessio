from home.models import Website, ChurchIndexEvent
from home.services.events_service import get_merged_church_schedules_list
from home.utils.date_utils import time_plus_hours


def index_events_for_website(website: Website):
    church_index_to_add = []

    website_churches = []
    for parish in website.parishes.all():
        for church in parish.churches.all():
            website_churches.append(church)
            church_index_to_add.append(ChurchIndexEvent(
                church=church,
                day=None,
                start_time=None,
                indexed_end_time=None,
                displayed_end_time=None,
                is_explicitely_other=None,
            ))

    all_church_events = []
    if not website.unreliability_reason:
        merged_church_schedules_list = get_merged_church_schedules_list(
            website, website_churches, day_filter=None, max_days=10
        )
        for church_events in merged_church_schedules_list.church_events_by_day.values():
            all_church_events += church_events

    for church_event in all_church_events:
        event_day = church_event.event.start.date()
        event_start_time = church_event.event.start.time()
        displayed_end_time = church_event.event.end.time() if church_event.event.end else None
        indexed_end_time = displayed_end_time or time_plus_hours(event_start_time, 4)
        if church_event.church:
            church_index_to_add.append(ChurchIndexEvent(
                church=church_event.church,
                day=event_day,
                start_time=event_start_time,
                indexed_end_time=indexed_end_time,
                displayed_end_time=displayed_end_time,
                is_explicitely_other=None,
            ))
        else:
            for church in website_churches:
                church_index_to_add.append(ChurchIndexEvent(
                    church=church,
                    day=event_day,
                    start_time=event_start_time,
                    indexed_end_time=indexed_end_time,
                    displayed_end_time=displayed_end_time,
                    is_explicitely_other=church_event.is_church_explicitly_other,
                ))

    # Remove existing events
    ChurchIndexEvent.objects.filter(church__in=website_churches).delete()

    for website_index_event in church_index_to_add:
        website_index_event.save()
