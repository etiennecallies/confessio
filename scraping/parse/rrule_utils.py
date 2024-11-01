from datetime import datetime, timedelta, time
from typing import Optional

from dateutil.rrule import rrule, rruleset, WEEKLY, DAILY, rrulestr

from home.utils.date_utils import get_current_year
from scraping.parse.explain_schedule import get_explanation_from_schedule
from scraping.parse.periods import rrules_from_period, PeriodEnum
from scraping.parse.schedules import ScheduleItem, SchedulesList, Event, RegularRule


def add_exrules(rset, periods, use_complementary: bool):
    current_year = get_current_year()
    for period in periods:
        for year in [current_year, current_year + 1]:
            for rule in rrules_from_period(period, year, use_complementary):
                rset.exrule(rrulestr(rule))


def get_rruleset_from_schedule(schedule: ScheduleItem, default_year: int) -> rruleset:
    rset = rruleset()

    if schedule.is_one_off_rule():
        dt_as_string = schedule.rule.get_start(default_year).strftime('%Y%m%dT%H%M%S')
        one_off_rrule = f"DTSTART:{dt_as_string}\nRRULE:FREQ=DAILY;UNTIL={dt_as_string}"

        if schedule.is_exception_rule:
            rset.exrule(rrulestr(one_off_rrule))
        else:
            rset.rrule(rrulestr(one_off_rrule))

        return rset

    if schedule.is_regular_rule():
        if schedule.is_exception_rule:
            rset.exrule(rrulestr(schedule.rule.rrule))
        else:
            rset.rrule(rrulestr(schedule.rule.rrule))

    add_exrules(rset, schedule.rule.include_periods, not schedule.is_exception_rule)
    add_exrules(rset, schedule.rule.exclude_periods, schedule.is_exception_rule)

    return rset


def get_events_from_schedule_item(schedule: ScheduleItem,
                                  start_date: datetime, end_date: datetime,
                                  default_year: int) -> list[Event]:
    rset = get_rruleset_from_schedule(schedule, default_year)

    events = []
    for start in rset.between(start_date, end_date):
        end = start + timedelta(minutes=schedule.duration_in_minutes) \
            if schedule.duration_in_minutes is not None else None
        events.append(Event(
            church_id=schedule.church_id,
            start=start,
            end=end
        ))

    return events


def get_events_from_schedule_items(schedules: list[ScheduleItem],
                                   start_date: datetime, end_date: datetime,
                                   default_year: int) -> list[Event]:
    all_events = sum((get_events_from_schedule_item(schedule, start_date, end_date, default_year)
                      for schedule in schedules), [])

    return list(sorted(list(set(all_events))))


#########
# CHECK #
#########

def are_schedule_rrules_valid(schedule: ScheduleItem) -> bool:
    try:
        get_rruleset_from_schedule(schedule, get_current_year())
        return True
    except ValueError as e:
        print(e)
        print(schedule)
        return False


def are_schedules_list_rrules_valid(schedules_list: SchedulesList) -> bool:
    return all(are_schedule_rrules_valid(schedule_item)
               for schedule_item in schedules_list.schedules)


def is_overnight_schedule(schedule: ScheduleItem) -> bool:
    if not schedule.duration_in_minutes:
        return False

    if schedule.duration_in_minutes > 18 * 60:
        return True

    rset = get_rruleset_from_schedule(schedule, get_current_year())
    dt_2000 = datetime(2000, 1, 1)
    start = rset.after(dt_2000)
    end = start + timedelta(minutes=schedule.duration_in_minutes)

    if end.time() <= time(hour=1):
        # If the schedule ends before 1am, it is not considered as overnight
        return False

    return start.date() != end.date()


def has_overnight_schedules(schedules_list: SchedulesList) -> bool:
    return any(is_overnight_schedule(schedule_item)
               for schedule_item in schedules_list.schedules)


def is_schedule_explainable(schedule: ScheduleItem) -> bool:
    try:
        get_explanation_from_schedule(schedule, get_current_year())
        return True
    except ValueError as e:
        print(e)
        print(schedule)
        return False


def is_schedules_list_explainable(schedules_list: SchedulesList) -> bool:
    return all(is_schedule_explainable(schedule_item)
               for schedule_item in schedules_list.schedules)


###########
# COMPARE #
###########

def are_schedules_list_equivalent(sl1: SchedulesList, sl2: SchedulesList,
                                  start_date: datetime, end_date: datetime
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

    events1 = get_events_from_schedule_items(sl1.schedules, start_date, end_date, default_year)
    events2 = get_events_from_schedule_items(sl2.schedules, start_date, end_date, default_year)

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
        rule=RegularRule(
            rrule='FREQ=WEEKLY;BYDAY=WE',
            include_periods=[],
            exclude_periods=[PeriodEnum.LENT]
        ),
        is_exception_rule=False,
        duration_in_minutes=60,
    )
    default_year_ = 2024
    rset_ = get_rruleset_from_schedule(schedule_, default_year_)
    print(rset_)
    for occurrence in rset_.between(datetime(2024, 1, 1),
                                    datetime(2024, 12, 31)):
        print(occurrence)

    rrule_ = 'DTSTART:20240106T100000\nRRULE:FREQ=WEEKLY;BYDAY=SA'
    rrulestr(rrule_)
