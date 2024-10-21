from datetime import timedelta
from enum import Enum

from dateutil.rrule import rrulestr, rrule

from home.utils.date_utils import format_datetime_with_locale
from scraping.parse.schedules import ScheduleItem


class Frequency(Enum):
    YEARLY = 0
    MONTHLY = 1
    WEEKLY = 2
    DAILY = 3
    HOURLY = 4
    MINUTELY = 5
    SECONDLY = 6


class Weekday(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


NAME_BY_WEEKDAY = {
    Weekday.MONDAY: "lundi",
    Weekday.TUESDAY: "mardi",
    Weekday.WEDNESDAY: "mercredi",
    Weekday.THURSDAY: "jeudi",
    Weekday.FRIDAY: "vendredi",
    Weekday.SATURDAY: "samedi",
    Weekday.SUNDAY: "dimanche",
}


def get_weekly_explanation(rstr: rrule) -> str:
    prefix = "toutes les semaines"

    weekdays = [NAME_BY_WEEKDAY[Weekday(w)] for w in rstr._byweekday]

    assert len(weekdays) > 0, "No weekday in weekly rrule"

    if len(weekdays) == 1:
        return f"{prefix} le {weekdays[0]}"

    return f"{prefix} les {', '.join(weekdays[:-1])} et {weekdays[-1]}"


def get_daily_explanation(rstr: rrule) -> str:
    if rstr._until:
        full_date = format_datetime_with_locale(rstr._dtstart, "%A %d %B %Y",
                                                'fr_FR.UTF-8')
        return f"le {full_date.lower()}"

    return "tous les jours"


def get_explanation_from_schedule(schedule: ScheduleItem) -> str:
    explanation = ''

    if schedule.rrule:
        rstr: rrule = rrulestr(schedule.rrule)
        frequency = Frequency(rstr._freq)
        if frequency == Frequency.WEEKLY:
            explanation += get_weekly_explanation(rstr)
        elif frequency == Frequency.DAILY:
            explanation += get_daily_explanation(rstr)
        else:
            raise NotImplementedError(f"Frequency {frequency} not implemented yet")

    dtstart = rstr._dtstart
    if schedule.duration_in_minutes:
        dtend = dtstart + timedelta(minutes=schedule.duration_in_minutes)
        explanation += f" de {dtstart.strftime('%H:%M')} à {dtend.strftime('%H:%M')}"
    else:
        explanation += f" à partir de {dtstart.strftime('%H:%M')}"

    return explanation


if __name__ == '__main__':
    schedule = ScheduleItem(
        church_id=None,
        rrule='DTSTART:20240102T173000\nRRULE:FREQ=WEEKLY;BYDAY=TU,WE,TH,FR',
        exrule=None,
        duration_in_minutes=60,
        include_periods=[],
        exclude_periods=[]
    )

    print(get_explanation_from_schedule(schedule))

    schedule = ScheduleItem(
        church_id=None,
        rrule='DTSTART:20240329T160000\nRRULE:FREQ=DAILY;UNTIL=20240329T170000',
        exrule=None,
        duration_in_minutes=60,
        include_periods=[],
        exclude_periods=[]
    )

    print(get_explanation_from_schedule(schedule))
