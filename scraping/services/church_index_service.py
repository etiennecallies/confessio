from datetime import datetime

from home.models import ChurchIndexEvent
from scraping.parse.schedules import Event


def event_from_church_index_event(church_index_event: ChurchIndexEvent) -> Event:
    start = datetime.combine(church_index_event.day, church_index_event.start_time)
    end = datetime.combine(church_index_event.day, church_index_event.displayed_end_time) \
        if church_index_event.displayed_end_time else None

    return Event(
        church_id=None,  # TODO this needs a refactoring
        start=start,
        end=end,
    )
