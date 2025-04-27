from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from home.models import Church, Website, ChurchIndexEvent
from home.services.website_schedules_service import ChurchEvent, ChurchSortedSchedules, \
    ChurchScheduleItem, get_merged_schedule_items, get_sorted_schedules_by_church_id, \
    do_display_explicit_other_churches, get_church_color_by_uuid
from home.services.holiday_zone_service import get_website_holiday_zone
from home.services.sources_service import get_website_sorted_parsings
from home.utils.date_utils import get_current_year, time_from_minutes
from scraping.parse.rrule_utils import get_events_from_schedule_item
from scraping.parse.schedules import Event
from scraping.services.parsing_service import get_church_by_id, get_parsing_schedules_list


@dataclass
class WebsiteEvents:
    church_events_by_day: dict[date, list[ChurchEvent]]
    page_range: str
    confession_exists: bool
    parsings_have_been_moderated: bool | None
    church_color_by_uuid: dict[UUID, str]  # ok, but we need to be iso with get churches
    display_explicit_other_churches: bool  # ok, but we need to be iso with get churches
    has_explicit_other_churches: bool
    has_unknown_churches: bool
    has_different_churches: bool

    def next_event_in_church(self, church: Church) -> Event | None:
        for church_events in self.church_events_by_day.values():
            for church_event in church_events:
                if church_event.church == church:
                    return church_event.event

        return None


def get_website_events(website: Website,
                       index_events: list[ChurchIndexEvent],
                       all_website_churches: list[Church],
                       day_filter: date | None = None,
                       hour_min: int | None = None,
                       hour_max: int | None = None,
                       max_days: int = 8
                       ) -> WebsiteEvents:
    ################
    # Get parsings #
    ################
    all_church_schedule_items = []

    if not day_filter:
        start_date = date.today()
        current_year = get_current_year()
        end_date = start_date + timedelta(days=300)
    else:
        start_date = day_filter
        current_year = start_date.year
        end_date = start_date
        max_days = 1

    min_time = max_time = None
    if hour_min or hour_max:
        min_time = time_from_minutes(hour_min or 0)
        max_time = time_from_minutes(hour_max or 24 * 60 - 1)

    holiday_zone = get_website_holiday_zone(website, all_website_churches)

    if website.unreliability_reason:
        parsings = []
    else:
        parsings = get_website_sorted_parsings(website)

    for i, parsing in enumerate(parsings):
        church_by_id = get_church_by_id(parsing, all_website_churches)

        schedules_list = get_parsing_schedules_list(parsing)
        if schedules_list is None:
            continue

        for schedule in schedules_list.schedules:
            if schedule.church_id is not None and schedule.church_id != -1 \
                    and schedule.church_id not in church_by_id:
                # We ignore schedule for out-of-scope churches
                continue

            if min_time or max_time:
                start_time = schedule.get_start_time() or min_time
                end_time = schedule.get_end_time() or max_time
                if start_time > max_time or end_time < min_time:
                    continue

            events = get_events_from_schedule_item(schedule, start_date,
                                                   current_year, holiday_zone,
                                                   end_date, max_days=max_days)
            if events:
                all_church_schedule_items.append(
                    ChurchScheduleItem.from_schedule_item(schedule, parsing, church_by_id, events)
                )

    merged_church_schedule_items = get_merged_schedule_items(all_church_schedule_items)
    # TODO we shall make sure the church_id are the same across all parsings
    church_by_id = {cs.schedule_item.item.church_id: cs.church
                    for cs in merged_church_schedule_items}

    ##############
    # Get events #
    ##############
    sorted_church_events = list(sorted(list(set(map(
        lambda index_event: ChurchEvent.from_index_event(index_event),
        [index_event for index_event in index_events if index_event.day is not None]
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

    ######################
    # Get schedule_items #
    ######################

    church_schedule_items = get_sorted_schedules_by_church_id(merged_church_schedule_items)
    church_sorted_schedules = [
        ChurchSortedSchedules.from_sorted_schedules(church_schedules, church_id, church_by_id)
        for church_id, church_schedules in church_schedule_items.items()
    ]

    churches_with_events = {cs.church for cs in merged_church_schedule_items}
    church_sorted_schedules += [
        ChurchSortedSchedules(
            church=c,
            is_church_explicitly_other=False,
            sorted_schedules=[]
        ) for c in all_website_churches if c not in churches_with_events
    ]

    display_explicit_other_churches = do_display_explicit_other_churches(church_sorted_schedules)
    all_church_events = sum(church_events_by_day.values(), [])
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
        confession_exists=len(sorted_church_events) > 0,
        parsings_have_been_moderated=parsings_have_been_moderated,
        church_color_by_uuid=get_church_color_by_uuid(church_sorted_schedules),
        display_explicit_other_churches=display_explicit_other_churches,
        has_explicit_other_churches=has_explicit_other_churches,
        has_unknown_churches=has_unknown_churches,
        has_different_churches=has_different_churches,
    )


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
