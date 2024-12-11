from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from home.models import Church, Parsing, Website
from home.utils.date_utils import get_current_year
from scraping.parse.rrule_utils import get_events_from_schedule_items
from scraping.parse.schedules import Event, ScheduleItem, SchedulesList, get_merged_schedules_list
from scraping.services.parse_pruning_service import get_parsing_schedules_list, get_church_by_id


@dataclass
class ChurchScheduleItem:
    church: Optional[Church]
    is_church_explicitly_other: bool
    schedule_item: ScheduleItem

    @classmethod
    def from_schedule_item(cls, schedule_item: ScheduleItem,
                           church_by_id: dict[int, Church]) -> 'ChurchScheduleItem':
        if schedule_item.church_id is None or schedule_item.church_id == -1:
            return cls(
                church=None,
                is_church_explicitly_other=schedule_item.church_id == -1,
                schedule_item=schedule_item,
            )

        return cls(
            church=church_by_id[schedule_item.church_id],
            is_church_explicitly_other=False,
            schedule_item=schedule_item,
        )


@dataclass
class ChurchEvent:
    church: Optional[Church]
    is_church_explicitly_other: bool
    event: Event

    @classmethod
    def from_event(cls, event: Event, church_by_id: dict[int, Church]) -> 'ChurchEvent':
        if event.church_id is None or event.church_id == -1:
            return cls(
                church=None,
                is_church_explicitly_other=event.church_id == -1,
                event=event,
            )

        return cls(
            church=church_by_id[event.church_id],
            is_church_explicitly_other=False,
            event=event,
        )


@dataclass
class ChurchSchedulesList:
    church_schedules: list[ChurchScheduleItem]
    schedules_list: SchedulesList

    @classmethod
    def from_parsing(cls, parsing: Parsing, website: Website) -> Optional['ChurchSchedulesList']:
        schedules_list = get_parsing_schedules_list(parsing)
        if schedules_list is None:
            return None

        church_by_id = get_church_by_id(parsing, website)
        church_schedules = [ChurchScheduleItem.from_schedule_item(schedule, church_by_id)
                            for schedule in schedules_list.schedules]

        return cls(
            church_schedules=church_schedules,
            schedules_list=schedules_list
        )

    def get_church_events(self) -> list[ChurchEvent]:
        max_events = 7
        start_date = datetime.now()
        end_date = start_date + timedelta(days=365)
        events = get_events_from_schedule_items(self.schedules_list.schedules, start_date, end_date,
                                                get_current_year(), max_events)
        church_by_id = {cs.schedule_item.church_id: cs.church for cs in self.church_schedules}

        return [ChurchEvent.from_event(event, church_by_id) for event in events[:max_events]]


def get_merged_church_schedules_list(csl: list[ChurchSchedulesList]
                                     ) -> ChurchSchedulesList:
    return ChurchSchedulesList(
        church_schedules=[cs for sl in csl for cs in sl.church_schedules],
        schedules_list=get_merged_schedules_list([cs.schedules_list for cs in csl])
    )
