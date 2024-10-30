from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from scraping.parse.periods import PeriodEnum


class OneOffRule(BaseModel, frozen=True):
    start_isoformat: str
    weekday: int | None

    def get_start(self) -> datetime:
        return datetime.strptime(self.start_isoformat, "%Y-%m-%dT%H:%M:%S")


class RegularRule(BaseModel, frozen=True):
    rrule: str
    include_periods: list[PeriodEnum]
    exclude_periods: list[PeriodEnum]

    def __hash__(self):
        """It would have been simpler to use tuple instead of list for include_periods and
        exclude_periods, but openapi schema generation does not support tuple (for now)."""
        return hash((
            tuple(sorted(self.model_dump(exclude={'include_periods', 'exclude_periods'}).items())),
            tuple(self.include_periods), tuple(self.exclude_periods)
        ))


class ScheduleItem(BaseModel, frozen=True):
    church_id: Optional[int]
    rule: OneOffRule | RegularRule
    is_exception_rule: bool
    duration_in_minutes: Optional[int]

    def is_one_off_rule(self) -> bool:
        return isinstance(self.rule, OneOffRule)

    def is_regular_rule(self) -> bool:
        return isinstance(self.rule, RegularRule)


class SchedulesList(BaseModel):
    schedules: list[ScheduleItem]
    possible_by_appointment: bool
    is_related_to_mass: bool
    is_related_to_adoration: bool
    is_related_to_permanence: bool
    will_be_seasonal_events: bool


class Event(BaseModel, frozen=True):
    church_id: Optional[int]
    start: datetime
    end: Optional[datetime]

    def __lt__(self, other: 'Event'):
        return self.start.__lt__(other.start)


def get_merged_schedules_list(sls: list[SchedulesList]) -> SchedulesList:
    return SchedulesList(
        schedules=[s for sl in sls for s in sl.schedules],
        possible_by_appointment=any(sl.possible_by_appointment for sl in sls),
        is_related_to_mass=any(sl.is_related_to_mass for sl in sls),
        is_related_to_adoration=any(sl.is_related_to_adoration for sl in sls),
        is_related_to_permanence=any(sl.is_related_to_permanence for sl in sls),
        will_be_seasonal_events=any(sl.will_be_seasonal_events for sl in sls),
    )
