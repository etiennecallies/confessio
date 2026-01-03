from datetime import date

from home.models import Church, Website, WebsiteModeration
from scheduling.models import IndexEvent
from scraping.services.website_moderation_service import remove_not_validated_moderation, \
    add_moderation


def website_has_schedules_conflict(church_index_events: list[IndexEvent]
                                   ) -> tuple[date, Church] | None:
    events_by_church_and_day = {}
    for church_event in church_index_events:
        if church_event.is_explicitely_other is not None:
            continue

        if church_event.displayed_end_time is None:
            continue

        for event in events_by_church_and_day.get((church_event.church.uuid, church_event.day), []):
            if event.start_time < church_event.displayed_end_time \
                    and event.displayed_end_time > church_event.start_time:
                return church_event.day, church_event.church

        events_by_church_and_day.setdefault((church_event.church.uuid, church_event.day), [])\
            .append(church_event)

    return None


def look_for_conflict(website: Website, church_index_events: list[IndexEvent]):
    conflict = website_has_schedules_conflict(church_index_events)
    if conflict is None:
        remove_not_validated_moderation(website,
                                        WebsiteModeration.Category.SCHEDULES_CONFLICT)
    else:
        conflict_day, conflict_church = conflict
        add_moderation(website, WebsiteModeration.Category.SCHEDULES_CONFLICT,
                       conflict_day=conflict_day, conflict_church=conflict_church)
