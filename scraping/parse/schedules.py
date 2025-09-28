from datetime import datetime, time, date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, model_validator, Field

from home.utils.date_utils import guess_year_from_weekday, Weekday, get_python_weekday
from scraping.parse.periods import PeriodEnum, LiturgicalDayEnum, get_liturgical_date


################
# ONE OFF RULE #
################

class OneOffRule(BaseModel, frozen=True):
    year: int | None
    month: int | None  # only nullable when liturgical_day is given
    day: int | None  # only nullable when liturgical_day is given
    weekday: Weekday | None
    liturgical_day: LiturgicalDayEnum | None

    @model_validator(mode='after')
    def validate_date_specification(self) -> 'OneOffRule':
        if (not self.month or not self.day) and not self.liturgical_day:
            raise ValueError('Either month and day, or liturgical_day must be provided')

        return self

    def is_valid_date(self) -> bool:
        try:
            if self.month and self.day:
                # check day and month
                datetime(2000, self.month, self.day)  # 2000 is a leap year

                # Check day and month with year
                if self.year:
                    datetime(self.year, self.month, self.day)

                # Check year and weekday
                if self.year and self.weekday is not None:
                    python_weekday = get_python_weekday(self.weekday)
                    if datetime(self.year, self.month, self.day).weekday() != python_weekday:
                        raise ValueError(f'Invalid weekday for {self}')

            return True
        except ValueError:
            return False

    def get_start(self, default_year: int) -> date:
        if self.liturgical_day:
            return get_liturgical_date(self.liturgical_day, self.year or default_year)

        if not self.year:
            if self.weekday is not None:
                year = guess_year_from_weekday(default_year, self.month, self.day, self.weekday)
            else:
                year = default_year
        else:
            year = self.year

        return date(year, self.month, self.day)

    def get_key(self):
        return self.year, self.month, self.day, self.weekday, self.liturgical_day

    def __lt__(self, other: 'OneOffRule') -> bool:
        return self.get_key() < other.get_key()


################
# REGULAR RULE #
################

class Position(Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4
    FIFTH = 5
    LAST = -1


class NWeekday(BaseModel, frozen=True):
    weekday: Weekday
    position: Position

    def __lt__(self, other: 'NWeekday') -> bool:
        return (self.weekday.value, self.position.value) < \
            (other.weekday.value, other.position.value)


class DailyRule(BaseModel, frozen=True):
    def __hash__(self):
        return hash('')


class WeeklyRule(BaseModel, frozen=True):
    by_weekdays: list[Weekday] = Field(..., description='uniqueItems')

    def __hash__(self):
        return hash(tuple(sorted(map(lambda w: w.value, self.by_weekdays))))


class MonthlyRule(BaseModel, frozen=True):
    by_nweekdays: list[NWeekday]

    def __hash__(self):
        return hash(tuple(sorted(self.by_nweekdays)))


class RegularRule(BaseModel, frozen=True):
    rule: DailyRule | WeeklyRule | MonthlyRule
    only_in_periods: list[PeriodEnum] = Field(..., description='uniqueItems')
    not_in_periods: list[PeriodEnum] = Field(..., description='uniqueItems')
    not_on_dates: list[OneOffRule] = Field(..., description='table')

    def __hash__(self):
        """It would have been simpler to use tuple instead of list for only_in_periods and
        not_in_periods, but openapi schema generation does not support tuple (for now)."""
        return hash((
            hash(self.rule),
            tuple(sorted(self.only_in_periods)),
            tuple(sorted(self.not_in_periods)),
            tuple(sorted(self.not_on_dates)),
        ))

    def is_daily_rule(self) -> bool:
        return isinstance(self.rule, DailyRule)

    def is_weekly_rule(self) -> bool:
        return isinstance(self.rule, WeeklyRule)

    def is_monthly_rule(self) -> bool:
        return isinstance(self.rule, MonthlyRule)


#############
# SCHEDULES #
#############

class ScheduleItem(BaseModel, frozen=True):
    church_id: int | None
    date_rule: OneOffRule | RegularRule
    is_cancellation: bool
    start_time_iso8601: str | None = Field(..., description='time')
    end_time_iso8601: str | None = Field(..., description='time')

    @model_validator(mode='after')
    def validate_times(self) -> 'ScheduleItem':
        self.get_start_time()
        self.get_end_time()

        return self

    def is_one_off_rule(self) -> bool:
        return isinstance(self.date_rule, OneOffRule)

    def is_regular_rule(self) -> bool:
        return isinstance(self.date_rule, RegularRule)

    def get_start_time(self) -> time | None:
        if self.start_time_iso8601 is None or self.start_time_iso8601 in ('', 'null'):
            return None

        return time.fromisoformat(self.start_time_iso8601)

    def get_end_time(self) -> time | None:
        if self.end_time_iso8601 is None or self.end_time_iso8601 in ('', 'null'):
            return None

        return time.fromisoformat(self.end_time_iso8601)


class SchedulesList(BaseModel):
    schedules: list[ScheduleItem]
    possible_by_appointment: bool = Field(..., description='checkbox')
    is_related_to_mass: bool = Field(..., description='checkbox')
    is_related_to_adoration: bool = Field(..., description='checkbox')
    is_related_to_permanence: bool = Field(..., description='checkbox')
    will_be_seasonal_events: bool = Field(..., description='checkbox')

    def __eq__(self, other: 'SchedulesList'):
        return self.model_dump(exclude={'schedules'}) == other.model_dump(exclude={'schedules'}) \
            and set(self.schedules) == set(other.schedules)


class Event(BaseModel, frozen=True):
    church_id: Optional[int]
    start: datetime
    end: Optional[datetime]

    def __lt__(self, other: 'Event'):
        return (self.start, self.church_id if self.church_id is not None else 100) \
            < (other.start, other.church_id if other.church_id is not None else 100)


def get_merged_schedules_list(sls: list[SchedulesList]) -> SchedulesList:
    return SchedulesList(
        schedules=[s for sl in sls for s in sl.schedules],
        possible_by_appointment=any(sl.possible_by_appointment for sl in sls),
        is_related_to_mass=any(sl.is_related_to_mass for sl in sls),
        is_related_to_adoration=any(sl.is_related_to_adoration for sl in sls),
        is_related_to_permanence=any(sl.is_related_to_permanence for sl in sls),
        will_be_seasonal_events=any(sl.will_be_seasonal_events for sl in sls),
    )
