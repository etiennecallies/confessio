from dataclasses import dataclass
from datetime import date, timedelta, datetime

from home.models import Church, ChurchIndexEvent


@dataclass
class ChurchEvent:
    church: Church | None
    is_church_explicitly_other: bool
    start: datetime
    end: datetime | None
    has_been_moderated: bool
    church_color: str

    @classmethod
    def from_index_event(cls, index_event: ChurchIndexEvent) -> 'ChurchEvent':
        start = datetime.combine(index_event.day, index_event.start_time)
        end = datetime.combine(index_event.day, index_event.displayed_end_time) \
            if index_event.displayed_end_time else None

        return cls(
            church=index_event.church if index_event.is_explicitely_other is None else None,
            is_church_explicitly_other=bool(index_event.is_explicitely_other),
            start=start,
            end=end,
            has_been_moderated=index_event.has_been_moderated,
            church_color=index_event.church_color,
        )

    def __lt__(self, other: 'ChurchEvent'):
        return (self.start, self.church_color) < (other.start, other.church_color)

    def __hash__(self):
        return hash((
            self.start,
            self.end,
            self.church_color
        ))


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
    events_truncated: bool

    def next_event_in_church(self, church: Church) -> ChurchEvent | None:
        for church_events in self.church_events_by_day.values():
            for church_event in church_events:
                if church_event.church == church:
                    return church_event

        return None


def get_website_events(index_events: list[ChurchIndexEvent],
                       events_truncated: bool,
                       unique_day: bool) -> WebsiteEvents:
    church_events_by_day = get_church_events_by_day(index_events, unique_day or events_truncated)

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
        events_truncated=events_truncated,
    )


########################
# CHURCH EVENTS BY DAY #
########################

def get_church_events_by_day(index_events: list[ChurchIndexEvent],
                             unique_day: bool) -> dict[date, list[ChurchEvent]]:
    today = date.today()
    sorted_church_events = list(sorted(list(set(map(
        lambda index_event: ChurchEvent.from_index_event(index_event),
        [index_event for index_event in index_events if index_event.day >= today]
    )))))

    max_days = 1 if unique_day else 8

    church_events_by_day = {}
    if sorted_church_events:
        first_day = sorted_church_events[0].start.date()
        for i in range(max_days):
            day = first_day + timedelta(days=i)
            church_events_by_day[day] = []

        for church_event in sorted_church_events:
            event_date = church_event.start.date()
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
