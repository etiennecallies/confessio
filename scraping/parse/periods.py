from datetime import date, timedelta
from enum import Enum

from dateutil.rrule import rrulestr

from home.utils.date_utils import get_current_day
from scraping.parse.holidays import HolidayZoneEnum, HOLIDAY_BY_ZONE


###################
# LITURGICAL DAYS #
###################

class LiturgicalDayEnum(str, Enum):
    ASH_WEDNESDAY = 'ash_wednesday'
    PALM_SUNDAY = 'palm_sunday'
    HOLY_MONDAY = 'holy_monday'
    HOLY_TUESDAY = 'holy_tuesday'
    HOLY_WEDNESDAY = 'holy_wednesday'
    MAUNDY_THURSDAY = 'maundy_thursday'
    GOOD_FRIDAY = 'good_friday'
    HOLY_SATURDAY = 'holy_saturday'
    EASTER_SUNDAY = 'easter_sunday'
    ASCENSION = 'ascension'
    PENTECOST = 'pentecost'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


# To be filled on year basis
EASTER_DATES_BY_YEAR = {
    2024: date(2024, 3, 31),
    2025: date(2025, 4, 20),
    2026: date(2026, 4, 5),
}


def get_easter_day(year: int) -> date:
    if year not in EASTER_DATES_BY_YEAR:
        raise ValueError(f'Easter day not implemented for year {year}')

    return EASTER_DATES_BY_YEAR[year]


def check_easter_dates() -> bool:
    # In september, we should have easter date for the next year
    future_date = get_current_day() + timedelta(days=365 + 4 * 30)
    future_year = future_date.year

    return future_year in EASTER_DATES_BY_YEAR


def get_offset(liturgical_day: LiturgicalDayEnum):
    if liturgical_day == LiturgicalDayEnum.ASH_WEDNESDAY:
        return -46
    if liturgical_day == LiturgicalDayEnum.PALM_SUNDAY:
        return -7
    if liturgical_day == LiturgicalDayEnum.HOLY_MONDAY:
        return -6
    if liturgical_day == LiturgicalDayEnum.HOLY_TUESDAY:
        return -5
    if liturgical_day == LiturgicalDayEnum.HOLY_WEDNESDAY:
        return -4
    if liturgical_day == LiturgicalDayEnum.MAUNDY_THURSDAY:
        return -3
    if liturgical_day == LiturgicalDayEnum.GOOD_FRIDAY:
        return -2
    if liturgical_day == LiturgicalDayEnum.HOLY_SATURDAY:
        return -1
    if liturgical_day == LiturgicalDayEnum.EASTER_SUNDAY:
        return 0
    if liturgical_day == LiturgicalDayEnum.ASCENSION:
        return 39
    if liturgical_day == LiturgicalDayEnum.PENTECOST:
        return 49


def get_liturgical_date(liturgical_day: LiturgicalDayEnum, year: int) -> date:
    easter_day = get_easter_day(year)
    offset = get_offset(liturgical_day)

    return easter_day + timedelta(days=offset)


###########
# PERIODS #
###########

class PeriodEnum(str, Enum):
    # Months
    JANUARY = 'january'
    FEBRUARY = 'february'
    MARCH = 'march'
    APRIL = 'april'
    MAY = 'may'
    JUNE = 'june'
    JULY = 'july'
    AUGUST = 'august'
    SEPTEMBER = 'september'
    OCTOBER = 'october'
    NOVEMBER = 'november'
    DECEMBER = 'december'

    # Seasons
    ADVENT = 'advent'
    LENT = 'lent'

    # Holidays
    SCHOOL_HOLIDAYS = 'school_holidays'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


def get_advent_dates(year: int) -> tuple[date, date]:
    christmas = date(year, 12, 25)
    # Find the fourth Sunday before Christmas
    advent_start = christmas - timedelta(days=christmas.weekday() + 22)
    return advent_start, christmas


#############
# INTERVALS #
#############

def intervals_from_period(period: PeriodEnum, year: int,
                          holiday_zone: HolidayZoneEnum) -> list[tuple[date, date]]:
    # Months
    if period == PeriodEnum.JANUARY:
        return [(date(year, 1, 1), date(year, 1, 31))]
    if period == PeriodEnum.FEBRUARY:
        # handle leap years
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            return [(date(year, 2, 1), date(year, 2, 29))]
        else:
            return [(date(year, 2, 1), date(year, 2, 28))]
    if period == PeriodEnum.MARCH:
        return [(date(year, 3, 1), date(year, 3, 31))]
    if period == PeriodEnum.APRIL:
        return [(date(year, 4, 1), date(year, 4, 30))]
    if period == PeriodEnum.MAY:
        return [(date(year, 5, 1), date(year, 5, 31))]
    if period == PeriodEnum.JUNE:
        return [(date(year, 6, 1), date(year, 6, 30))]
    if period == PeriodEnum.JULY:
        return [(date(year, 7, 1), date(year, 7, 31))]
    if period == PeriodEnum.AUGUST:
        return [(date(year, 8, 1), date(year, 8, 31))]
    if period == PeriodEnum.SEPTEMBER:
        return [(date(year, 9, 1), date(year, 9, 30))]
    if period == PeriodEnum.OCTOBER:
        return [(date(year, 10, 1), date(year, 10, 31))]
    if period == PeriodEnum.NOVEMBER:
        return [(date(year, 11, 1), date(year, 11, 30))]
    if period == PeriodEnum.DECEMBER:
        return [(date(year, 12, 1), date(year, 12, 31))]

    # Seasons
    if period == PeriodEnum.ADVENT:
        return [get_advent_dates(year)]

    if period == PeriodEnum.LENT:
        return [(get_liturgical_date(LiturgicalDayEnum.ASH_WEDNESDAY, year),
                 get_liturgical_date(LiturgicalDayEnum.HOLY_SATURDAY, year))]

    # Holidays
    if period == PeriodEnum.SCHOOL_HOLIDAYS:
        if holiday_zone not in HOLIDAY_BY_ZONE:
            raise ValueError(f'School holidays not implemented for zone {holiday_zone}')

        period_by_year = HOLIDAY_BY_ZONE[holiday_zone]
        if year not in period_by_year:
            raise ValueError(f'School holidays not implemented for year {year} in '
                             f'zone {holiday_zone}')

        return period_by_year[year]

    raise ValueError(f'Period {period} not implemented')


def compute_intervals_complementary(intervals: list[tuple[date, date]],
                                    start_year: int, end_year: int
                                    ) -> list[tuple[date, date]]:
    sorted_intervals = sorted(intervals)

    # Get the full year
    full_start = date(start_year, 1, 1)
    full_end = date(end_year, 12, 31)

    # Compute the complementary
    complementary = []
    for start, end in sorted_intervals:
        if full_start < start:
            complementary.append((full_start, start))
        full_start = end
    if full_start < full_end:
        complementary.append((full_start, full_end))

    return complementary


def add_interval(interval: tuple[date, date],
                 intervals: list[tuple[date, date]]) -> list[tuple[date, date]]:
    start, end = interval
    for i, (i_start, i_end) in enumerate(intervals):
        if i_start <= start <= i_end or i_start <= end <= i_end:
            return add_interval((min(i_start, start), max(i_end, end)),
                                [*intervals[:i], *intervals[i + 1:]])

    intervals.append((start, end))

    return intervals


def compute_union_of_all_intervals(intervals: list[tuple[date, date]]) -> list[tuple[date, date]]:
    result_intervals = []
    for interval in intervals:
        result_intervals = add_interval(interval, result_intervals)

    return result_intervals


def rrules_from_intervals(intervals: list[tuple[date, date]]) -> list[str]:
    return [f'DTSTART:{start.strftime("%Y%m%d")}\n'
            f'RRULE:FREQ=DAILY;UNTIL={end.strftime("%Y%m%d")}'
            for start, end in intervals]


def add_exrules(rset, periods, start_year, end_year, use_complementary: bool,
                holiday_zone: HolidayZoneEnum):
    if not periods:
        return

    all_intervals = []
    for period in periods:
        for year in range(start_year, end_year + 1):
            all_intervals += intervals_from_period(period, year, holiday_zone)

    merged_intervals = compute_union_of_all_intervals(all_intervals)
    if use_complementary:
        merged_intervals = compute_intervals_complementary(merged_intervals,
                                                           start_year, end_year)

    for rule in rrules_from_intervals(merged_intervals):
        rset.exrule(rrulestr(rule))
