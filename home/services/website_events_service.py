from dataclasses import dataclass
from datetime import date, timedelta

from home.models import Church, ChurchIndexEvent
from home.services.website_schedules_service import ChurchEvent
from scraping.parse.schedules import Event


@dataclass
class WebsiteEvents:
    church_events_by_day: dict[date, list[ChurchEvent]]
    page_range: str
    confession_exists: bool
    parsings_have_been_moderated: bool | None
    display_explicit_other_churches: bool
    has_explicit_other_churches: bool
    has_unknown_churches: bool
    has_different_churches: bool

    def next_event_in_church(self, church: Church) -> Event | None:
        for church_events in self.church_events_by_day.values():
            for church_event in church_events:
                if church_event.church == church:
                    return church_event.event

        return None


def get_website_events(index_events: list[ChurchIndexEvent]) -> WebsiteEvents:
    church_events_by_day = get_church_events_by_day(index_events)

    all_church_events = sum(church_events_by_day.values(), [])
    confession_exists = len(all_church_events) > 0
    display_explicit_other_churches = all(ce.is_church_explicitly_other for ce in all_church_events)
    parsings_have_been_moderated = all(ce.has_been_moderated for ce in all_church_events) \
        if all_church_events else None
    has_explicit_other_churches = display_explicit_other_churches and \
        any(c.is_church_explicitly_other for c in all_church_events)
    has_unknown_churches = any(c.church is None and not c.is_church_explicitly_other
                               for c in all_church_events)
    has_different_churches = len(set(c.church for c in all_church_events if c.church)) > 1

    return WebsiteEvents(
        church_events_by_day=church_events_by_day,
        page_range=get_page_range(church_events_by_day),
        confession_exists=confession_exists,
        parsings_have_been_moderated=parsings_have_been_moderated,
        display_explicit_other_churches=display_explicit_other_churches,
        has_explicit_other_churches=has_explicit_other_churches,
        has_unknown_churches=has_unknown_churches,
        has_different_churches=has_different_churches,
    )


########################
# CHURCH EVENTS BY DAY #
########################

def get_church_events_by_day(index_events: list[ChurchIndexEvent],
                             max_days: int = 8) -> dict[date, list[ChurchEvent]]:
    today = date.today()
    sorted_church_events = list(sorted(list(set(map(
        lambda index_event: ChurchEvent.from_index_event(index_event),
        [index_event for index_event in index_events if index_event.day >= today]
    )))))

    church_events_by_day = {}
    if sorted_church_events:
        first_day = sorted_church_events[0].event.start.date()
        for i in range(max_days):
            day = first_day + timedelta(days=i)
            church_events_by_day[day] = []

        for church_event in sorted_church_events:
            event_date = church_event.event.start.date()
            if event_date in church_events_by_day:
                church_events_by_day[event_date].append(church_event)

    return church_events_by_day


#########
# PAGES #
#########

def get_page_range(church_events_by_day: dict[date, list[ChurchEvent]]) -> str:
    dates_per_page = 4
    if len(church_events_by_day) < dates_per_page:
        return '1'

    first_day = min(church_events_by_day.keys())
    for i in range(dates_per_page, len(church_events_by_day)):
        if church_events_by_day[first_day + timedelta(days=i)]:
            return '12'

    return '1'
