import locale
from datetime import datetime

from django.utils.timezone import make_aware


def datetime_to_ts_us(dt: datetime) -> int:
    return int(dt.timestamp() * 1000000.0)


def ts_us_to_datetime(timestamp_us):
    return make_aware(datetime.fromtimestamp(timestamp_us / 1000000.0))


def get_year_start(year: int):
    return datetime(year, 1, 1)


def get_year_end(year: int):
    return datetime(year, 12, 31, 23, 59, 59)


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


if __name__ == '__main__':
    ts_us = datetime_to_ts_us(datetime.now())
    print(ts_us)
    print(ts_us_to_datetime(ts_us))
