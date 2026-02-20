from dataclasses import dataclass
from datetime import date, timedelta

from registry.models import Church
from scheduling.models import IndexEvent


@dataclass
class WebsiteEvents:
    index_events_by_day: dict[date, list[IndexEvent]]
    page_range: str
    confession_exists: bool
    parsings_have_been_moderated: bool | None
    display_explicit_other_churches: bool
    has_explicit_other_churches: bool
    has_unknown_churches: bool
    has_different_churches: bool
    events_truncated: bool

    def next_event_in_church(self, church: Church) -> IndexEvent | None:
        for index_events in self.index_events_by_day.values():
            for index_event in index_events:
                if index_event.church == church:
                    return index_event

        return None


def get_website_events(index_events: list[IndexEvent],
                       events_truncated: bool,
                       unique_day: bool) -> WebsiteEvents:
    index_events_by_day = get_index_events_by_day(index_events, unique_day)

    all_index_events = sum(index_events_by_day.values(), [])
    confession_exists = len(all_index_events) > 0
    display_explicit_other_churches = all(ie.is_explicitely_other for ie in all_index_events)
    parsings_have_been_moderated = all(ie.has_been_moderated for ie in all_index_events) \
        if all_index_events else None
    has_explicit_other_churches = display_explicit_other_churches and \
        any(c.is_explicitely_other for c in all_index_events)
    has_unknown_churches = any(c.church is None and not c.is_explicitely_other
                               for c in all_index_events)
    has_different_churches = len(set(c.church for c in all_index_events if c.church)) > 1

    return WebsiteEvents(
        index_events_by_day=index_events_by_day,
        page_range=get_page_range(index_events_by_day),
        confession_exists=confession_exists,
        parsings_have_been_moderated=parsings_have_been_moderated,
        display_explicit_other_churches=display_explicit_other_churches,
        has_explicit_other_churches=has_explicit_other_churches,
        has_unknown_churches=has_unknown_churches,
        has_different_churches=has_different_churches,
        events_truncated=events_truncated,
    )


########################
# INDEX EVENTS BY DAY #
########################

def get_index_events_by_day(index_events: list[IndexEvent],
                            unique_day: bool) -> dict[date, list[IndexEvent]]:
    today = date.today()
    sorted_index_events = list(sorted(list(set(
        index_event for index_event in index_events if index_event.day >= today
    ))))

    max_days = 1 if unique_day else 8

    index_events_by_day = {}
    if sorted_index_events:
        first_day = sorted_index_events[0].day
        for i in range(max_days):
            day = first_day + timedelta(days=i)
            index_events_by_day[day] = []

        for index_event in sorted_index_events:
            if index_event.day in index_events_by_day:
                index_events_by_day[index_event.day].append(index_event)

    return index_events_by_day


#########
# PAGES #
#########

def get_page_range(index_events_by_day: dict[date, list[IndexEvent]]) -> str:
    dates_per_page = 4
    if len(index_events_by_day) < dates_per_page:
        return '1'

    first_day = min(index_events_by_day.keys())
    for i in range(dates_per_page, len(index_events_by_day)):
        if index_events_by_day[first_day + timedelta(days=i)]:
            return '12'

    return '1'
