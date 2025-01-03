from datetime import date
from enum import Enum

from dateutil.rrule import rrulestr


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


def get_liturgical_date(liturgical_day: LiturgicalDayEnum, year: int) -> date:
    if year == 2024:
        if liturgical_day == LiturgicalDayEnum.ASH_WEDNESDAY:
            return date(year, 2, 26)
        if liturgical_day == LiturgicalDayEnum.PALM_SUNDAY:
            return date(year, 4, 5)
        if liturgical_day == LiturgicalDayEnum.HOLY_MONDAY:
            return date(year, 4, 6)
        if liturgical_day == LiturgicalDayEnum.HOLY_TUESDAY:
            return date(year, 4, 7)
        if liturgical_day == LiturgicalDayEnum.HOLY_WEDNESDAY:
            return date(year, 4, 8)
        if liturgical_day == LiturgicalDayEnum.MAUNDY_THURSDAY:
            return date(year, 4, 9)
        if liturgical_day == LiturgicalDayEnum.GOOD_FRIDAY:
            return date(year, 4, 10)
        if liturgical_day == LiturgicalDayEnum.HOLY_SATURDAY:
            return date(year, 4, 11)
        if liturgical_day == LiturgicalDayEnum.EASTER_SUNDAY:
            return date(year, 4, 12)
        if liturgical_day == LiturgicalDayEnum.ASCENSION:
            return date(year, 5, 21)
        if liturgical_day == LiturgicalDayEnum.PENTECOST:
            return date(year, 5, 31)

        raise ValueError(f'Liturgical day {liturgical_day} not implemented')

    if year == 2025:
        if liturgical_day == LiturgicalDayEnum.ASH_WEDNESDAY:
            return date(year, 2, 18)
        if liturgical_day == LiturgicalDayEnum.PALM_SUNDAY:
            return date(year, 3, 29)
        if liturgical_day == LiturgicalDayEnum.HOLY_MONDAY:
            return date(year, 3, 30)
        if liturgical_day == LiturgicalDayEnum.HOLY_TUESDAY:
            return date(year, 3, 31)
        if liturgical_day == LiturgicalDayEnum.HOLY_WEDNESDAY:
            return date(year, 4, 1)
        if liturgical_day == LiturgicalDayEnum.MAUNDY_THURSDAY:
            return date(year, 4, 2)
        if liturgical_day == LiturgicalDayEnum.GOOD_FRIDAY:
            return date(year, 4, 3)
        if liturgical_day == LiturgicalDayEnum.HOLY_SATURDAY:
            return date(year, 4, 4)
        if liturgical_day == LiturgicalDayEnum.EASTER_SUNDAY:
            return date(year, 4, 5)
        if liturgical_day == LiturgicalDayEnum.ASCENSION:
            return date(year, 5, 14)
        if liturgical_day == LiturgicalDayEnum.PENTECOST:
            return date(year, 5, 24)

        raise ValueError(f'Liturgical day {liturgical_day} not implemented')

    raise ValueError(f'Liturgical dates not implemented for year {year}')


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


def intervals_from_period(period: PeriodEnum, year: int) -> list[tuple[date, date]]:
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
        if year == 2026:
            return [(date(year, 11, 30), date(year, 12, 24))]
        elif year == 2025:
            return [(date(year, 11, 29), date(year, 12, 24))]

        raise ValueError(f'Advent not implemented for year {year}')

    if period == PeriodEnum.LENT:
        if year == 2026:
            return [(date(year, 3, 6), date(year, 4, 20))]
        elif year == 2025:
            return [(date(year, 2, 26), date(year, 4, 11))]

        raise ValueError(f'Lent not implemented for year {year}')

    # Holidays
    if period == PeriodEnum.SCHOOL_HOLIDAYS:
        # TODO handle zones
        if year == 2024:
            return [(date(year, 2, 10), date(year, 2, 24)),
                    (date(year, 4, 6), date(year, 4, 22)),
                    (date(year, 7, 6), date(year, 9, 2)),
                    (date(year, 10, 19), date(year, 11, 4)),
                    (date(year, 12, 21), date(year + 1, 1, 6))]
        elif year == 2025:
            return [(date(year, 2, 23), date(year, 3, 9)),
                    (date(year, 4, 19), date(year, 5, 5)),
                    (date(year, 7, 5), date(year, 8, 31)),
                    (date(year, 10, 18), date(year, 11, 3)),
                    (date(year, 12, 20), date(year + 1, 1, 5))]
        elif year == 2026:
            return [(date(year, 2, 10), date(year, 2, 24)),
                    (date(year, 4, 6), date(year, 4, 22)),
                    (date(year, 7, 6), date(year, 9, 2)),
                    (date(year, 10, 19), date(year, 11, 4)),
                    (date(year, 12, 21), date(year + 1, 1, 6))]

        raise ValueError(f'School holidays not implemented for year {year}')

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


def add_exrules(rset, periods, start_year, end_year, use_complementary: bool):
    if not periods:
        return

    all_intervals = []
    for period in periods:
        for year in range(start_year, end_year + 1):
            all_intervals += intervals_from_period(period, year)

    merged_intervals = compute_union_of_all_intervals(all_intervals)
    if use_complementary:
        merged_intervals = compute_intervals_complementary(merged_intervals,
                                                           start_year, end_year)

    for rule in rrules_from_intervals(merged_intervals):
        rset.exrule(rrulestr(rule))
