from datetime import datetime, time, date
from typing import Optional

from pydantic import BaseModel, model_validator

from home.utils.date_utils import guess_year_from_weekday
from scraping.parse.periods import PeriodEnum, LiturgicalDayEnum, get_liturgical_date


class OneOffRule(BaseModel, frozen=True):
    year: int | None
    month: int | None  # only nullable when liturgical_day is given
    day: int | None  # only nullable when liturgical_day is given
    weekday_iso8601: int | None
    liturgical_day: LiturgicalDayEnum | None

    @model_validator(mode='after')
    def validate_date(self) -> 'OneOffRule':
        if (not self.month or not self.day) and not self.liturgical_day:
            raise ValueError(f'Missing month or day for {self}')

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
                if self.year and self.weekday_iso8601 is not None:
                    python_weekday = self.weekday_iso8601 - 1
                    if datetime(self.year, self.month, self.day).weekday() != python_weekday:
                        raise ValueError(f'Invalid weekday for {self}')

            return True
        except ValueError:
            return False

    def get_start(self, default_year: int) -> date:
        if self.liturgical_day:
            return get_liturgical_date(self.liturgical_day, self.year or default_year)

        if not self.year:
            if self.weekday_iso8601 is not None:
                year = guess_year_from_weekday(default_year, self.month, self.day,
                                               self.weekday_iso8601)
            else:
                year = default_year
        else:
            year = self.year

        return date(year, self.month, self.day)


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
    church_id: int | None
    date_rule: OneOffRule | RegularRule
    is_cancellation: bool
    start_time_iso8601: str | None
    end_time_iso8601: str | None

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
        if self.start_time_iso8601 is None:
            return

        return time.fromisoformat(self.start_time_iso8601)

    def get_end_time(self) -> time | None:
        if self.end_time_iso8601 is None:
            return None

        return time.fromisoformat(self.end_time_iso8601)


class SchedulesList(BaseModel):
    schedules: list[ScheduleItem]
    possible_by_appointment: bool
    is_related_to_mass: bool
    is_related_to_adoration: bool
    is_related_to_permanence: bool
    will_be_seasonal_events: bool

    def __eq__(self, other: 'SchedulesList'):
        return self.model_dump(exclude={'schedules'}) == other.model_dump(exclude={'schedules'}) \
            and set(self.schedules) == set(other.schedules)


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
