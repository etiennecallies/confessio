import locale
from datetime import datetime, date

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


#########
# OTHER #
#########

def is_29th_february(month: int, day: int) -> bool:
    return month == 2 and day == 29


def is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def guess_year_from_weekday(default_year: int, month: int, day: int, weekday_iso8601: int) -> int:
    start_date = datetime(2000, month, day)  # 2000 is a leap year
    weekday_python = weekday_iso8601 - 1

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
                     f"for month {month}, day {day}, weekday {weekday_iso8601}")


if __name__ == '__main__':
    ts_us = datetime_to_ts_us(datetime.now())
    print(ts_us)
    print(ts_us_to_datetime(ts_us))
