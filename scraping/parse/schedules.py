import json
from datetime import datetime, time, date
from enum import Enum
from typing import Optional

from dateutil.rrule import rrulestr
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

    def is_valid_date(self) -> bool:
        if (not self.month or not self.day) and not self.liturgical_day:
            return False

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

    def __lt__(self, other: 'OneOffRule') -> bool:
        """Compare OneOffRule objects based on their start date."""
        return self.model_dump() < other.model_dump()


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
        return (self.weekday, self.position) < (other.weekday, other.position)


class DailyRule(BaseModel, frozen=True):
    def __hash__(self):
        return hash('')


class WeeklyRule(BaseModel, frozen=True):
    by_weekdays: list[Weekday] = Field(..., description='table')

    def __hash__(self):
        return hash(tuple(sorted(map(lambda w: w.value, self.by_weekdays))))


class MonthlyRule(BaseModel, frozen=True):
    by_nweekdays: list[NWeekday]

    def __hash__(self):
        return hash(tuple(sorted(self.by_nweekdays)))


class RegularRule(BaseModel, frozen=True):
    rule: DailyRule | WeeklyRule | MonthlyRule
    only_in_periods: list[PeriodEnum] = Field(..., description='table')
    not_in_periods: list[PeriodEnum] = Field(..., description='table')
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


###################
# TEMP CONVERSION #
###################


WEEKDAY_BY_INT = {
    0: Weekday.MONDAY,
    1: Weekday.TUESDAY,
    2: Weekday.WEDNESDAY,
    3: Weekday.THURSDAY,
    4: Weekday.FRIDAY,
    5: Weekday.SATURDAY,
    6: Weekday.SUNDAY,
}


def temp_convert_weekly_rule(rstr: rrulestr) -> WeeklyRule:
    weekdays = [WEEKDAY_BY_INT[w] for w in rstr._byweekday]

    return WeeklyRule(
        by_weekdays=weekdays
    )


def temp_convert_monthly_rule(rstr: rrulestr, old_rrule: str) -> MonthlyRule:
    if rstr._bynweekday:
        return MonthlyRule(
            by_nweekdays=[NWeekday(weekday=WEEKDAY_BY_INT[w], position=Position(position))
                          for w, position in rstr._bynweekday]
        )
    elif rstr._byweekday:
        by_days = [WEEKDAY_BY_INT[w] for w in rstr._byweekday]

        if len(by_days) > 1:
            raise ValueError("Multiple weekdays in monthly rrule not implemented yet")

        by_day = by_days[0]

        if not rstr._bysetpos:
            raise ValueError("No set position in monthly rrule")
        by_set_positions = [Position(p) for p in rstr._bysetpos]

        return MonthlyRule(
            by_nweekdays=[NWeekday(weekday=by_day, position=p) for p in by_set_positions]
        )

    raise ValueError("Unknown monthly rrule", old_rrule)


class Frequency(Enum):
    YEARLY = 0
    MONTHLY = 1
    WEEKLY = 2
    DAILY = 3
    HOURLY = 4
    MINUTELY = 5
    SECONDLY = 6


def temp_convert_rrule_dict(old_rrule: str) -> DailyRule | WeeklyRule | MonthlyRule:
    rstr = rrulestr(old_rrule)

    if not rstr._dtstart:
        raise ValueError("No start date in rrule")

    frequency = Frequency(rstr._freq)
    if frequency == Frequency.WEEKLY or (frequency == Frequency.DAILY and rstr._byweekday):
        return temp_convert_weekly_rule(rstr)
    elif frequency == Frequency.DAILY:
        return DailyRule()
    elif frequency == Frequency.MONTHLY:
        return temp_convert_monthly_rule(rstr, old_rrule)
    else:
        raise ValueError(f"Frequency {frequency} not implemented yet")


def temp_convert_date_rule_dict(old_dict: dict) -> OneOffRule | RegularRule:
    if 'rule' in old_dict or 'rrule' in old_dict:
        if 'rrule' in old_dict:
            old_dict['rule'] = temp_convert_rrule_dict(old_dict.pop('rrule')).model_dump()
            if 'include_periods' in old_dict:
                old_dict['only_in_periods'] = old_dict.pop('include_periods')
            if 'exclude_periods' in old_dict:
                old_dict['not_in_periods'] = old_dict.pop('exclude_periods')
            old_dict['not_on_dates'] = []
            return RegularRule(**old_dict)
        else:
            return RegularRule(**old_dict)
    else:
        if 'weekday_iso8601' in old_dict:
            weekday_iso8601 = old_dict.pop('weekday_iso8601')
            old_dict['weekday'] = WEEKDAY_BY_INT[weekday_iso8601 - 1] \
                if weekday_iso8601 is not None else None
        return OneOffRule(**old_dict)


def temp_convert_schedule_dict(old_dict: dict) -> ScheduleItem:
    old_dict['date_rule'] = temp_convert_date_rule_dict(old_dict['date_rule']).model_dump()
    return ScheduleItem(**old_dict)


def temp_convert_schedules_list_dict(old_dict: dict) -> SchedulesList:
    old_dict['schedules'] = [temp_convert_schedule_dict(sched).model_dump()
                             for sched in old_dict['schedules']]
    return SchedulesList(**old_dict)


def temp_convert_schedules_list_json(old_json: str) -> str:
    old_dict = json.loads(old_json)
    return temp_convert_schedules_list_dict(old_dict).model_dump_json()


if __name__ == '__main__':
    nweekday = NWeekday(weekday=Weekday.MONDAY, position=Position.FIRST)
    print(nweekday.model_dump_json())