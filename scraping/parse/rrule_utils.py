from datetime import datetime, time, date, timedelta
from typing import Optional

from dateutil.rrule import rrule, rruleset, WEEKLY, DAILY, rrulestr

from home.utils.date_utils import get_current_year, date_to_datetime, Weekday
from scraping.parse.explain_schedule import get_explanation_from_schedule
from scraping.parse.holidays import HolidayZoneEnum
from scraping.parse.intervals import add_exrules, add_exdate
from scraping.parse.liturgical import PeriodEnum
from scraping.parse.schedules import ScheduleItem, SchedulesList, Event, RegularRule, WeeklyRule, \
    MonthlyRule, CustomPeriod

####################
# RRULE GENERATION #
####################

BYDAY_BY_WEEKDAY = {
    Weekday.MONDAY: 'MO',
    Weekday.TUESDAY: 'TU',
    Weekday.WEDNESDAY: 'WE',
    Weekday.THURSDAY: 'TH',
    Weekday.FRIDAY: 'FR',
    Weekday.SATURDAY: 'SA',
    Weekday.SUNDAY: 'SU',
}


def get_rrule_of_rule(regular_rule: RegularRule) -> str:
    if regular_rule.is_daily_rule():
        return 'FREQ=DAILY'
    if isinstance(regular_rule.rule, WeeklyRule):
        return 'FREQ=WEEKLY;BYDAY=' + ','.join(map(lambda w: BYDAY_BY_WEEKDAY[w],
                                                   regular_rule.rule.by_weekdays))
    if isinstance(regular_rule.rule, MonthlyRule):
        return 'FREQ=MONTHLY;BYDAY=' + ','.join(map(
            lambda nw: f'{nw.position.value}{BYDAY_BY_WEEKDAY[nw.weekday]}',
            regular_rule.rule.by_nweekdays))

    raise ValueError(f"Frequency not implemented for rule: {regular_rule}")


def get_rrule_from_regular_rule(regular_rule: RegularRule, default_year: int) -> str:
    return f"DTSTART:{default_year}0101\nRRULE:{get_rrule_of_rule(regular_rule)}"


def get_rruleset_from_schedule(schedule: ScheduleItem, default_year: int,
                               holiday_zone: HolidayZoneEnum) -> rruleset:
    rset = rruleset()

    if schedule.is_one_off_rule():
        dt_as_string = schedule.date_rule.get_date(default_year).strftime('%Y%m%d')
        one_off_rrule = f"DTSTART:{dt_as_string}\nRRULE:FREQ=DAILY;UNTIL={dt_as_string}"

        if schedule.is_cancellation:
            rset.exrule(rrulestr(one_off_rrule))
        else:
            rset.rrule(rrulestr(one_off_rrule))

        return rset

    if schedule.is_regular_rule():
        rrule_at_default_year = get_rrule_from_regular_rule(schedule.date_rule, default_year)
        rrule_str = rrulestr(rrule_at_default_year)
        if schedule.is_cancellation:
            rset.exrule(rrule_str)
        else:
            rset.rrule(rrule_str)

    start_year = default_year
    end_year = default_year + 1
    add_exrules(rset, schedule.date_rule.only_in_periods, start_year, end_year,
                use_complementary=not schedule.is_cancellation, holiday_zone=holiday_zone)
    add_exrules(rset, schedule.date_rule.not_in_periods, start_year, end_year,
                use_complementary=schedule.is_cancellation, holiday_zone=holiday_zone)
    for one_off_rule in schedule.date_rule.not_on_dates:
        add_exdate(rset, one_off_rule, start_year, end_year)

    return rset


#####################
# EVENTS GENERATION #
#####################

def get_events_from_schedule_item(schedule: ScheduleItem,
                                  start_date: date,
                                  default_year: int,
                                  holiday_zone: HolidayZoneEnum,
                                  end_date: date | None = None,
                                  max_events: int | None = None,
                                  max_days: int | None = None) -> list[Event]:
    """
    end_date is inclusive
    """
    if schedule.is_one_off_rule() and not schedule.date_rule.is_valid_date():
        return []

    if schedule.get_start_time() is None:
        return []

    assert end_date is None or end_date >= start_date
    assert end_date is not None or max_days is not None or max_events is not None

    start_datetime = date_to_datetime(start_date)
    end_datetime = date_to_datetime(end_date) if end_date else None

    rset = get_rruleset_from_schedule(schedule, default_year, holiday_zone)

    events = []
    for one_date in rset.xafter(start_datetime, count=max_events, inc=True):
        if end_datetime is not None and one_date > end_datetime:
            break

        if max_days is not None:
            end_datetime = one_date + timedelta(days=max_days - 1)
            max_days = None

        start_time = schedule.get_start_time()
        start_dt = one_date.replace(hour=start_time.hour, minute=start_time.minute)

        end_dt = None
        end_time = schedule.get_end_time()
        if end_time is not None:
            end_dt = one_date.replace(hour=end_time.hour, minute=end_time.minute)

        events.append(Event(
            church_id=schedule.church_id,
            start=start_dt,
            end=end_dt
        ))

    return events


def get_events_from_schedule_items(schedules: list[ScheduleItem],
                                   start_date: date,
                                   default_year: int,
                                   holiday_zone: HolidayZoneEnum,
                                   end_date: date | None = None,
                                   max_events: int = None,
                                   max_days: int = None) -> list[Event]:
    all_events = sum((get_events_from_schedule_item(schedule, start_date, default_year,
                                                    holiday_zone, end_date,
                                                    max_events, max_days)
                      for schedule in schedules), [])

    return list(sorted(list(set(all_events))))


#########
# CHECK #
#########

def is_schedule_date_rule_valid(schedule: ScheduleItem) -> bool:
    if schedule.is_one_off_rule():
        return True

    try:
        default_holiday_zone = HolidayZoneEnum.FR_ZONE_A  # We do not need the accurate holiday zone
        get_rruleset_from_schedule(schedule, get_current_year(), default_holiday_zone)
        return True
    except ValueError as e:
        print(e)
        print(schedule)
        return False


def are_schedules_list_date_rule_valid(schedules_list: SchedulesList) -> bool:
    return all(is_schedule_date_rule_valid(schedule_item)
               for schedule_item in schedules_list.schedules)


def is_schedule_explainable(schedule: ScheduleItem) -> tuple[bool, Optional[str]]:
    try:
        get_explanation_from_schedule(schedule)
        return True, None
    except ValueError as e:
        print(e)
        print(schedule)
        return False, f'schedule: {schedule}, error: {str(e)}'


def is_schedules_list_explainable(schedules_list: SchedulesList) -> tuple[bool, Optional[str]]:
    for schedule_item in schedules_list.schedules:
        is_explainable, error = is_schedule_explainable(schedule_item)
        if not is_explainable:
            return False, error
    return True, None


##########
# REDUCE #
##########

def is_valid_schedule(schedule: ScheduleItem) -> bool:
    if (not schedule.is_cancellation
            and (schedule.get_start_time() is None
                 or schedule.get_start_time() == time(0, 0))):
        # we ignore schedules with no start time or with start time at midnight
        return False

    if schedule.is_one_off_rule():
        if not schedule.date_rule.is_valid():
            return False

    return True


def is_valid_period(period: PeriodEnum | CustomPeriod) -> bool:
    if isinstance(period, PeriodEnum):
        return True

    if isinstance(period, CustomPeriod):
        return period.start.is_valid() and period.end.is_valid()

    raise ValueError(f'Period of type {period} not implemented')


def get_valid_schedule(schedule: ScheduleItem) -> ScheduleItem:
    if schedule.is_regular_rule():
        return schedule.model_copy(
            update={
                'date_rule': schedule.date_rule.model_copy(
                    update={
                        'only_in_periods': [
                            period for period in schedule.date_rule.only_in_periods
                            if is_valid_period(period)],
                        'not_in_periods': [
                            period for period in schedule.date_rule.not_in_periods
                            if is_valid_period(period)
                        ],
                        'not_on_dates': [
                            one_off_rule for one_off_rule in schedule.date_rule.not_on_dates
                            if one_off_rule.is_valid()],
                    }
                )
            }
        )

    return schedule


def filter_valid_schedules(schedules: list[ScheduleItem]) -> list[ScheduleItem]:
    return [get_valid_schedule(schedule)
            for schedule in schedules if is_valid_schedule(schedule)]


###########
# COMPARE #
###########

def are_schedules_list_equivalent(sl1: SchedulesList, sl2: SchedulesList,
                                  start_date: date, end_date: date, holiday_zone: HolidayZoneEnum
                                  ) -> tuple[bool, Optional[str]]:
    default_year = start_date.year

    if sl1.is_related_to_mass != sl2.is_related_to_mass:
        return False, 'is_related_to_mass differs'

    if sl1.is_related_to_adoration != sl2.is_related_to_adoration:
        return False, 'is_related_to_adoration differs'

    if sl1.is_related_to_permanence != sl2.is_related_to_permanence:
        return False, 'is_related_to_permanence differs'

    if sl1.will_be_seasonal_events != sl2.will_be_seasonal_events:
        return False, 'will_be_seasonal_events differs'

    if sl1.possible_by_appointment != sl2.possible_by_appointment:
        return False, 'possible_by_appointment differs'

    if set(sl1.schedules) == set(sl2.schedules):
        return True, None

    events1 = get_events_from_schedule_items(sl1.schedules, start_date, default_year, holiday_zone,
                                             end_date)
    events2 = get_events_from_schedule_items(sl2.schedules, start_date, default_year, holiday_zone,
                                             end_date)

    if set(events1) == set(events2):
        return True, None

    return False, 'events differ'


if __name__ == '__main__':
    # Create a rruleset
    rules_ = rruleset()

    # Rule: Every Wednesday
    weekly_rule = rrule(WEEKLY, dtstart=datetime(2024, 1, 1, 10, 30),
                        byweekday=2)  # Every Wednesday
    rules_.rrule(weekly_rule)
    print(str(weekly_rule))

    # Exclusion Rule: Nothing in August
    # Exclude every day in August
    august_exrule = rrule(DAILY, dtstart=datetime(2024, 8, 1),
                          until=datetime(2024, 8, 31))
    rules_.exrule(august_exrule)
    print(str(august_exrule))

    # Print occurrences between two dates
    for occurrence in rules_.between(datetime(2024, 1, 1),
                                     datetime(2024, 12, 31)):
        print(occurrence)

    schedule_ = ScheduleItem(
        church_id=1,
        date_rule=RegularRule(
            rrule='DTSTART:20000101\nRRULE:FREQ=MONTHLY;BYDAY=SU',
            # rrule='DTSTART:20240101T170000\nRRULE:FREQ=DAILY;BYHOUR=17;BYMINUTE=0',
            # rrule='DTSTART:20000101\nRRULE:FREQ=DAILY',
            only_in_periods=[],
            not_in_periods=[]
        ),
        is_cancellation=False,
        start_time_iso8601='16:00:00',
        end_time_iso8601=None,
    )
    default_year_ = 2024
    rset_ = get_rruleset_from_schedule(schedule_, default_year_, HolidayZoneEnum.FR_ZONE_B)
    print(rset_)
    for occurrence in rset_.between(datetime(2024, 1, 1),
                                    datetime(2024, 12, 31)):
        print(occurrence)

    rrule_ = 'DTSTART:20240106T100000\nRRULE:FREQ=WEEKLY;BYDAY=SA'
    rrulestr(rrule_)
