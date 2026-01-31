import locale
from datetime import datetime, date, time
from enum import Enum

from django.utils.timezone import make_aware


##############
# CONVERSION #
##############

def datetime_to_ts_us(dt: datetime) -> int:
    return int(dt.timestamp() * 1000000.0)


def ts_us_to_datetime(timestamp_us):
    return make_aware(datetime.fromtimestamp(timestamp_us / 1000000.0))


def date_to_datetime(d: date) -> datetime:
    return datetime(d.year, d.month, d.day)


def time_from_minutes(minutes: int) -> time:
    hours, minutes = divmod(minutes, 60)
    return time(hour=hours, minute=minutes)


def time_plus_hours(t: time, hours: int) -> time:
    total_minutes = min(t.hour * 60 + t.minute + hours * 60, 24 * 60 - 1)
    return time_from_minutes(total_minutes)


#################
# RELATIVE DATE #
#################

def get_current_day() -> date:
    return date.today()


def get_current_year() -> int:
    return datetime.now().year


def get_year_start(year: int) -> date:
    return date(year, 1, 1)


def get_year_end(year: int) -> date:
    return date(year, 12, 31)


##########
# FORMAT #
##########

def format_datetime_with_locale(dt: datetime, dt_format: str, locale_name: str) -> str:
    current_locale = locale.getlocale(locale.LC_TIME)

    try:
        locale.setlocale(locale.LC_TIME, locale_name)
        formatted_date = dt.strftime(dt_format)
    finally:
        locale.setlocale(locale.LC_TIME, current_locale)

    return formatted_date


###########
# WEEKDAY #
###########

class Weekday(Enum):
    MONDAY = 'monday'
    TUESDAY = 'tuesday'
    WEDNESDAY = 'wednesday'
    THURSDAY = 'thursday'
    FRIDAY = 'friday'
    SATURDAY = 'saturday'
    SUNDAY = 'sunday'


PYTHON_WEEKDAY = {
    Weekday.MONDAY: 0,
    Weekday.TUESDAY: 1,
    Weekday.WEDNESDAY: 2,
    Weekday.THURSDAY: 3,
    Weekday.FRIDAY: 4,
    Weekday.SATURDAY: 5,
    Weekday.SUNDAY: 6,
}


def get_python_weekday(weekday: Weekday) -> int:
    return PYTHON_WEEKDAY[weekday]


def is_29th_february(month: int, day: int) -> bool:
    return month == 2 and day == 29


def is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def guess_year_from_weekday(default_year: int, month: int, day: int, weekday: Weekday) -> int:
    start_date = datetime(2000, month, day)  # 2000 is a leap year
    weekday_python = get_python_weekday(weekday)

    for year in [default_year, default_year + 1]:
        if is_29th_february(month, day) and not is_leap_year(year):
            continue
        if start_date.replace(year=year).weekday() == weekday_python:
            return year

    max_count = 28  # 28 years is the maximum difference between two years with the same weekday
    for year_count in range(1, max_count + 1):
        year = default_year - year_count

        if is_29th_february(month, day) and not is_leap_year(year):
            continue
        if start_date.replace(year=year).weekday() == weekday_python:
            return year

    raise ValueError(f"Could not find a date between year {default_year - max_count} "
                     f"and year {default_year + 1} "
                     f"for month {month}, day {day}, weekday {weekday}")


if __name__ == '__main__':
    ts_us = datetime_to_ts_us(datetime.now())
    print(ts_us)
    print(ts_us_to_datetime(ts_us))
