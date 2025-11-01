from datetime import date

from dateutil.rrule import rrulestr

from scraping.parse.holidays import HolidayZoneEnum, HOLIDAY_BY_ZONE
from scraping.parse.liturgical import PeriodEnum, get_advent_dates, get_liturgical_date, \
    LiturgicalDayEnum, get_solemnities_dates
from scraping.parse.schedules import CustomPeriod


def intervals_from_period(period: PeriodEnum, year: int,
                          holiday_zone: HolidayZoneEnum) -> list[tuple[date, date]]:
    # Seasons
    if period == PeriodEnum.SUMMER:
        return [(date(year, 7, 1), date(year, 8, 31))]
    if period == PeriodEnum.WINTER:
        return [
            (date(year, 1, 1), date(year, 6, 30)),
            (date(year, 9, 1), date(year, 12, 31)),
        ]

    # Liturgical seasons
    if period == PeriodEnum.ADVENT:
        return [get_advent_dates(year)]

    if period == PeriodEnum.LENT:
        return [(get_liturgical_date(LiturgicalDayEnum.ASH_WEDNESDAY, year),
                 get_liturgical_date(LiturgicalDayEnum.HOLY_SATURDAY, year))]

    if period == PeriodEnum.SOLEMNITIES:
        return [(d, d) for d in get_solemnities_dates(year)]

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


def interval_from_custom_period(custom_period: CustomPeriod, year: int) -> tuple[date, date]:
    return custom_period.start.get_date(year), custom_period.end.get_date(year)


def intervals_from_period_or_custom_period(period: PeriodEnum | CustomPeriod, year: int,
                                           holiday_zone: HolidayZoneEnum
                                           ) -> list[tuple[date, date]]:
    if isinstance(period, PeriodEnum):
        return intervals_from_period(period, year, holiday_zone)

    if isinstance(period, CustomPeriod):
        return [interval_from_custom_period(period, year)]

    raise ValueError(f'Period of type {period} not implemented')


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


def add_exrules(rset, periods: list[PeriodEnum | CustomPeriod], start_year, end_year,
                use_complementary: bool, holiday_zone: HolidayZoneEnum):
    if not periods:
        return

    all_intervals = []
    for period in periods:
        for year in range(start_year, end_year + 1):
            all_intervals += intervals_from_period_or_custom_period(period, year, holiday_zone)

    merged_intervals = compute_union_of_all_intervals(all_intervals)
    if use_complementary:
        merged_intervals = compute_intervals_complementary(merged_intervals,
                                                           start_year, end_year)

    for rule in rrules_from_intervals(merged_intervals):
        rset.exrule(rrulestr(rule))
