from datetime import datetime

from dateutil.rrule import rrule, rruleset, WEEKLY, DAILY, rrulestr

from scraping.parse.schedules import ScheduleItem, SchedulesList


def get_rruleset_from_schedule(schedule: ScheduleItem) -> rruleset:
    rset = rruleset()

    if schedule.rdates:
        rset.rdate(rrulestr(schedule.rdates))

    if schedule.exdates:
        rset.exdate(rrulestr(schedule.exdates))

    if schedule.rrules:
        rset.rrule(rrulestr(schedule.rrules))

    if schedule.exrules:
        rset.exrule(rrulestr(schedule.exrules))

    return rset


def are_schedule_rrules_valid(schedule: ScheduleItem) -> bool:
    try:
        get_rruleset_from_schedule(schedule)
        return True
    except ValueError:
        return False


def are_schedules_list_rrules_valid(schedules_list: SchedulesList) -> bool:
    return all(are_schedule_rrules_valid(schedule_item)
               for schedule_item in schedules_list.schedules)


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

    schedule = ScheduleItem(
        church_id=1,
        rdates='2024-01-01T10:30',
        # exdates='2024-08-01',
        exdates='',
        # rrules='FREQ=WEEKLY;BYDAY=WE',
        rrules='',
        # exrules='FREQ=DAILY;UNTIL=2024-08-31',
        exrules='',
        duration_in_minutes=60,
        during_school_holidays=True
    )
    rset_ = get_rruleset_from_schedule(schedule)
    print(rset_)
    for occurrence in rset_.between(datetime(2024, 1, 1),
                                    datetime(2024, 12, 31)):
        print(occurrence)
