from datetime import datetime, time
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
        dt_as_string = schedule.date_rule.get_start(default_year).strftime('%Y%m%d')
        one_off_rrule = f"DTSTART:{dt_as_string}\nRRULE:FREQ=DAILY;UNTIL={dt_as_string}"

        if schedule.is_cancellation:
            rset.exrule(rrulestr(one_off_rrule))
        else:
            rset.rrule(rrulestr(one_off_rrule))

        return rset

    if schedule.is_regular_rule():
        rrule_str = rrulestr(schedule.date_rule.rrule)
        if schedule.is_cancellation:
            rset.exrule(rrule_str)
        else:
            rset.rrule(rrule_str)

    add_exrules(rset, schedule.date_rule.include_periods, not schedule.is_cancellation)
    add_exrules(rset, schedule.date_rule.exclude_periods, schedule.is_cancellation)

    return rset


def get_events_from_schedule_item(schedule: ScheduleItem,
                                  start_date: datetime, end_date: datetime,
                                  default_year: int) -> list[Event]:
    if schedule.is_one_off_rule() and not schedule.date_rule.is_valid_date():
        return []

    rset = get_rruleset_from_schedule(schedule, default_year)

    events = []
    for one_date in rset.between(start_date, end_date):
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
                                   start_date: datetime, end_date: datetime,
                                   default_year: int) -> list[Event]:
    all_events = sum((get_events_from_schedule_item(schedule, start_date, end_date, default_year)
                      for schedule in schedules), [])

    return list(sorted(list(set(all_events))))


#########
# CHECK #
#########

def are_schedule_rrules_valid(schedule: ScheduleItem) -> bool:
    if schedule.is_one_off_rule():
        return True

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


def is_schedule_explainable(schedule: ScheduleItem) -> bool:
    try:
        get_explanation_from_schedule(schedule)
        return True
    except ValueError as e:
        print(e)
        print(schedule)
        return False


def is_schedules_list_explainable(schedules_list: SchedulesList) -> bool:
    return all(is_schedule_explainable(schedule_item)
               for schedule_item in schedules_list.schedules)


##########
# REDUCE #
##########

def is_necessary_schedule(schedule: ScheduleItem) -> bool:
    if not schedule.is_cancellation and schedule.get_start_time() == time(0, 0):
        return False

    return True


def filter_unnecessary_schedules(schedules: list[ScheduleItem]) -> list[ScheduleItem]:
    return [schedule for schedule in schedules if is_necessary_schedule(schedule)]


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
        date_rule=RegularRule(
            rrule='DTSTART:20240101T170000\nRRULE:FREQ=DAILY;BYHOUR=17;BYMINUTE=0',
            # rrule='DTSTART:20000101\nRRULE:FREQ=DAILY',
            include_periods=[],
            exclude_periods=[PeriodEnum.AUGUST]
        ),
        is_cancellation=False,
        start_time_iso8601='16:00:00',
        end_time_iso8601=None,
    )
    default_year_ = 2024
    rset_ = get_rruleset_from_schedule(schedule_, default_year_)
    print(rset_)
    for occurrence in rset_.between(datetime(2024, 1, 1),
                                    datetime(2024, 12, 31)):
        print(occurrence)

    rrule_ = 'DTSTART:20240106T100000\nRRULE:FREQ=WEEKLY;BYDAY=SA'
    rrulestr(rrule_)
