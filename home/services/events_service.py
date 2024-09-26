from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from home.models import Church, Parsing
from scraping.parse.schedules import Event, ScheduleItem, SchedulesList
from scraping.parse.test_rrule import get_events_from_schedule_items
from scraping.services.parse_pruning_service import get_parsing_schedules_list, get_church_by_id


@dataclass
class ChurchScheduleItem:
    church: Optional[Church]
    schedule_item: ScheduleItem

    @classmethod
    def from_schedule_item(cls, schedule_item: ScheduleItem,
                           church_by_id: dict[int, Church]) -> 'ChurchScheduleItem':
        church = church_by_id[schedule_item.church_id] \
            if schedule_item.church_id is not None else None

        return cls(
            church=church,
            schedule_item=schedule_item,
        )


@dataclass
class ChurchEvent:
    church: Optional[Church]
    event: Event

    @classmethod
    def from_event(cls, event: Event, church_by_id: dict[int, Church]) -> 'ChurchEvent':
        church = church_by_id[event.church_id] if event.church_id is not None else None

        return cls(
            church=church,
            event=event,
        )


@dataclass
class ChurchSchedulesList:
    church_schedules: list[ChurchScheduleItem]
    schedules_list: SchedulesList

    @classmethod
    def from_parsing(cls, parsing: Parsing) -> Optional['ChurchSchedulesList']:
        schedules_list = get_parsing_schedules_list(parsing)
        if schedules_list is None:
            return None

        church_by_id = get_church_by_id(parsing)
        church_schedules = [ChurchScheduleItem.from_schedule_item(schedule, church_by_id)
                            for schedule in schedules_list.schedules]

        return cls(
            church_schedules=church_schedules,
            schedules_list=schedules_list
        )

    def get_church_events(self) -> list[ChurchEvent]:
        start_date = datetime.now()
        end_date = start_date + timedelta(days=365)
        events = get_events_from_schedule_items(self.schedules_list.schedules, start_date, end_date)
        church_by_id = {cs.schedule_item.church_id: cs.church for cs in self.church_schedules}

        return [ChurchEvent.from_event(event, church_by_id) for event in events[:7]]


def get_merged_church_schedules_list(csl: list[ChurchSchedulesList]
                                     ) -> ChurchSchedulesList:
    return ChurchSchedulesList(
        church_schedules=[cs for sl in csl for cs in sl.church_schedules],
        schedules_list=SchedulesList(
            schedules=[s for sl in csl for s in sl.schedules_list.schedules],
            possible_by_appointment=any(sl.schedules_list.possible_by_appointment for sl in csl),
            is_related_to_mass=any(sl.schedules_list.is_related_to_mass for sl in csl),
            is_related_to_adoration=any(sl.schedules_list.is_related_to_adoration for sl in csl),
            is_related_to_permanence=any(sl.schedules_list.is_related_to_permanence for sl in csl),
            has_seasonal_events=any(sl.schedules_list.has_seasonal_events for sl in csl),
        )
    )
