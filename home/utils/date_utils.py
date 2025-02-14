import locale
from datetime import datetime, date, timedelta

from django.utils.timezone import make_aware


def datetime_to_ts_us(dt: datetime) -> int:
    return int(dt.timestamp() * 1000000.0)


def ts_us_to_datetime(timestamp_us):
    return make_aware(datetime.fromtimestamp(timestamp_us / 1000000.0))


def date_to_datetime(d: date) -> datetime:
    return datetime(d.year, d.month, d.day)


def datetime_to_date(dt: datetime) -> date:
    return date(dt.year, dt.month, dt.day)


def datetime_to_hour_iso8601(dt: datetime | None) -> str | None:
    if dt is None:
        return None

    return dt.strftime('%H:%M:%S')


def get_year_start(year: int) -> date:
    return date(year, 1, 1)


def get_year_end(year: int) -> date:
    return date(year, 12, 31)


def get_next_two_month(d: date) -> date:
    if d.month == 12:
        return date(d.year + 1, 2, 1)

    if d.month == 11:
        return date(d.year + 1, 1, 1)

    return date(d.year, d.month + 2, 1)


def get_end_of_next_month() -> date:
    first_of_next_two_months = get_next_two_month(date.today())

    return first_of_next_two_months - timedelta(days=1)


def get_current_week_and_next_two_weeks() -> list[list[date]]:
    today = date.today()
    current_week_start = today - timedelta(days=today.weekday())

    current_week = [current_week_start + timedelta(days=i) for i in range(7)]
    next_week = [current_week_start + timedelta(days=7 + i) for i in range(7)]
    next_two_week = [current_week_start + timedelta(days=14 + i) for i in range(7)]

    return [current_week, next_week, next_two_week]


def get_current_day() -> date:
    return date.today()


def get_current_year() -> int:
    return datetime.now().year


def format_datetime_with_locale(dt: datetime, dt_format: str, locale_name: str) -> str:
    current_locale = locale.getlocale(locale.LC_TIME)

    try:
        locale.setlocale(locale.LC_TIME, locale_name)
        formatted_date = dt.strftime(dt_format)
    finally:
        locale.setlocale(locale.LC_TIME, current_locale)

    return formatted_date


def guess_year_from_weekday(default_year: int, month: int, day: int, weekday_iso8601: int) -> int:
    start_date = datetime(default_year, month, day)
    weekday_python = weekday_iso8601 - 1

    for year in [default_year, default_year + 1]:
        if start_date.replace(year=year).weekday() == weekday_python:
            return year

    max_count = 28  # 28 years is the maximum difference between two years with the same weekday
    for year_count in range(1, max_count + 1):
        year = default_year - year_count
        if start_date.replace(year=year).weekday() == weekday_python:
            return year

    raise ValueError(f"Could not find a date between year {default_year - max_count} "
                     f"and year {default_year + 1} "
                     f"for month {month}, day {day}, weekday {weekday_iso8601}")


if __name__ == '__main__':
    ts_us = datetime_to_ts_us(datetime.now())
    print(ts_us)
    print(ts_us_to_datetime(ts_us))
