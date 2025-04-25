from datetime import date

from home.models import Website, Church
from home.services.events_service import get_merged_church_schedules_list


def website_has_schedules_conflict(website: Website) -> tuple[date, Church] | None:
    if website.unreliability_reason:
        return None

    website_churches = []
    for parish in website.parishes.all():
        for church in parish.churches.all():
            website_churches.append(church)

    merged_church_schedules_list = get_merged_church_schedules_list(
        website, website_churches, day_filter=None, max_days=300
    )
    for day, church_events in merged_church_schedules_list.church_events_by_day.items():
        events_by_church_id = {}
        for church_event in church_events:
            if not church_event.church:
                continue

            if not church_event.event.end:
                continue

            for event in events_by_church_id.get(church_event.event.church_id, []):
                if event.start < church_event.event.end and event.end > church_event.event.start:
                    return day, church_event.church

            events_by_church_id.setdefault(church_event.event.church_id, [])\
                .append(church_event.event)

    return None
