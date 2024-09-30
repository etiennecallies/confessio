from datetime import date
from enum import Enum


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
        if year == 2024:
            return [(date(year, 11, 30), date(year, 12, 24))]
        elif year == 2025:
            return [(date(year, 11, 29), date(year, 12, 24))]

        raise ValueError(f'Advent not implemented for year {year}')

    if period == PeriodEnum.LENT:
        if year == 2024:
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
                    (date(year, 10, 19), date(year, 11, 4))]
        elif year == 2025:
            return [(date(year, 2, 23), date(year, 3, 9)),
                    (date(year, 4, 19), date(year, 5, 5)),
                    (date(year, 7, 5), date(year, 8, 31)),
                    (date(year, 10, 18), date(year, 11, 3))]

        raise ValueError(f'School holidays not implemented for year {year}')

    raise ValueError(f'Period {period} not implemented')


def compute_intervals_complementary(intervals: list[tuple[date, date]], year: int
                                    ) -> list[tuple[date, date]]:
    # Get the full year
    full_year = [(date(year, 1, 1), date(year, 12, 31))]

    # Compute the complementary
    complementary = []
    for full_start, full_end in full_year:
        for start, end in intervals:
            if full_start < start:
                complementary.append((full_start, start))
            full_start = end
        if full_start < full_end:
            complementary.append((full_start, full_end))

    return complementary


def rrules_from_intervals(intervals: list[tuple[date, date]]) -> list[str]:
    return [f'DTSTART:{start.strftime("%Y%m%d")}T000000\n'
            f'RRULE:FREQ=DAILY;UNTIL={end.strftime("%Y%m%d")}T000000'
            for start, end in intervals]


def rrules_from_period(period: PeriodEnum, year: int, use_complementary: bool) -> list[str]:
    intervals = intervals_from_period(period, year)
    if use_complementary:
        intervals = compute_intervals_complementary(intervals, year)

    return rrules_from_intervals(intervals)
