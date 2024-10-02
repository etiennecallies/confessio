from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from scraping.parse.periods import PeriodEnum


class ScheduleItem(BaseModel, frozen=True):
    church_id: Optional[int]
    rrule: Optional[str]
    exrule: Optional[str]
    duration_in_minutes: Optional[int]
    include_periods: list[PeriodEnum]
    exclude_periods: list[PeriodEnum]

    def __hash__(self):
        """It would have been simpler to use tuple instead of list for include_periods and
        exclude_periods, but openapi schema generation does not support tuple (for now)."""
        return hash((
            tuple(sorted(self.model_dump(exclude={'include_periods', 'exclude_periods'}).items())),
            tuple(self.include_periods), tuple(self.exclude_periods)
        ))


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
