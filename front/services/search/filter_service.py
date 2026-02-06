from datetime import timedelta, date

from scheduling.utils.date_utils import get_current_day


def get_date_and_selected_day(day: date, day_filter: date | None) -> dict:
    return {
        'date': day,
        'is_selected': False if day_filter is None else day == day_filter,
    }


def get_filter_days(day_filter: date | None) -> dict:
    current_day = get_current_day()
    return {
        'any_day': {
            'is_selected': day_filter is None,
        },
        'current_day': get_date_and_selected_day(current_day, day_filter),
        'tomorrow': get_date_and_selected_day(current_day + timedelta(days=1), day_filter),
        'next_days': [get_date_and_selected_day(current_day + timedelta(days=i), day_filter)
                      for i in range(2, 8)],
    }
