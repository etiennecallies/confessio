from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, model_validator

from home.utils.date_utils import guess_year_from_weekday
from scraping.parse.periods import PeriodEnum


class OneOffRule(BaseModel, frozen=True):
    year: int | None
    month: int
    day: int
    weekday_iso8601: int | None
    hour: int
    minute: int

    @model_validator(mode='after')
    def validate_date(self) -> 'OneOffRule':
        # check day and month
        datetime(2000, self.month, self.day)  # 2000 is a leap year

        # Check day and month with year
        if self.year:
            datetime(self.year, self.month, self.day)

        # Check year and weekday
        if self.year and self.weekday_iso8601 is not None:
            if datetime(self.year, self.month, self.day).weekday() != self.weekday_iso8601 - 1:
                raise ValueError(f'Invalid weekday for {self}')

        return self

    @model_validator(mode='after')
    def validate_time(self) -> 'OneOffRule':
        # check hour and minute
        time(self.hour, self.minute)

        return self

    def get_start(self, default_year: int) -> datetime:
        if not self.year:
            if self.weekday_iso8601 is not None:
                year = guess_year_from_weekday(default_year, self.month, self.day,
                                               self.weekday_iso8601)
            else:
                year = default_year
        else:
            year = self.year

        return datetime(year, self.month, self.day, self.hour, self.minute)


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
