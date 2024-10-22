from datetime import timedelta
from enum import Enum

from dateutil.rrule import rrulestr, rrule

from home.utils.date_utils import format_datetime_with_locale
from home.utils.list_utils import enumerate_with_and
from scraping.parse.periods import PeriodEnum
from scraping.parse.schedules import ScheduleItem


#########
# ENUMS #
#########

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


class Position(Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4
    FIFTH = 5
    LAST = -1


################
# TRANSLATIONS #
################

NAME_BY_WEEKDAY = {
    Weekday.MONDAY: "lundi",
    Weekday.TUESDAY: "mardi",
    Weekday.WEDNESDAY: "mercredi",
    Weekday.THURSDAY: "jeudi",
    Weekday.FRIDAY: "vendredi",
    Weekday.SATURDAY: "samedi",
    Weekday.SUNDAY: "dimanche",
}

NAME_BY_POSITION = {
    Position.FIRST: "premier",
    Position.SECOND: "deuxième",
    Position.THIRD: "troisième",
    Position.FOURTH: "quatrième",
    Position.FIFTH: "cinquième",
    Position.LAST: "dernier",
}

NAME_BY_PERIOD = {
    PeriodEnum.JANUARY: 'en janvier',
    PeriodEnum.FEBRUARY: 'en février',
    PeriodEnum.MARCH: 'en mars',
    PeriodEnum.APRIL: 'en avril',
    PeriodEnum.MAY: 'en mai',
    PeriodEnum.JUNE: 'en juin',
    PeriodEnum.JULY: 'en juillet',
    PeriodEnum.AUGUST: 'en août',
    PeriodEnum.SEPTEMBER: 'en septembre',
    PeriodEnum.OCTOBER: 'en octobre',
    PeriodEnum.NOVEMBER: 'en novembre',
    PeriodEnum.DECEMBER: 'en décembre',

    # Seasons
    PeriodEnum.ADVENT: 'pendant l\'avent',
    PeriodEnum.LENT: 'pendant le carême',

    # Holidays
    PeriodEnum.SCHOOL_HOLIDAYS: 'pendant les vacances scolaires',
}


def get_weekly_explanation(rstr: rrule) -> str:
    prefix = "toutes les semaines"

    weekdays = [NAME_BY_WEEKDAY[Weekday(w)] for w in rstr._byweekday]

    if not weekdays:
        raise ValueError("No weekday in weekly rrule")

    article = "le" if len(weekdays) == 1 else "les"

    return f"{prefix} {article} {enumerate_with_and(weekdays)}"


def get_daily_explanation(rstr: rrule) -> str:
    if rstr._until:
        full_date = format_datetime_with_locale(rstr._dtstart, "%A %d %B %Y",
                                                'fr_FR.UTF-8')
        return f"le {full_date.lower()}"

    return "tous les jours"


def get_monthly_explanation(rstr: rrule) -> str:
    by_days = [Weekday(w) for w in rstr._byweekday]
    if not by_days:
        raise ValueError("No weekday in monthly rrule")

    if len(by_days) > 1:
        raise ValueError("Multiple weekdays in monthly rrule not implemented yet")

    by_set_positions = [NAME_BY_POSITION[Position(p)] for p in rstr._bysetpos]
    if not by_set_positions:
        raise ValueError("No set position in monthly rrule")

    article = "le" if len(by_set_positions) == 1 else "les"

    return f"{article} {enumerate_with_and(by_set_positions)} {NAME_BY_WEEKDAY[by_days[0]]} du mois"


def get_explanation_from_schedule(schedule: ScheduleItem) -> str:
    explanation = ''

    if schedule.rrule:
        rstr: rrule = rrulestr(schedule.rrule)

        dt_start = rstr._dtstart
        if not dt_start:
            raise ValueError("No start date in rrule")

        frequency = Frequency(rstr._freq)
        if frequency == Frequency.WEEKLY:
            explanation += get_weekly_explanation(rstr)
        elif frequency == Frequency.DAILY:
            explanation += get_daily_explanation(rstr)
        elif frequency == Frequency.MONTHLY:
            explanation += get_monthly_explanation(rstr)
        else:
            raise ValueError(f"Frequency {frequency} not implemented yet")

        if schedule.duration_in_minutes:
            dt_end = dt_start + timedelta(minutes=schedule.duration_in_minutes)
            explanation += f" de {dt_start.strftime('%H:%M')} à {dt_end.strftime('%H:%M')}"
        else:
            explanation += f" à partir de {dt_start.strftime('%H:%M')}"

    if schedule.include_periods:
        periods = [NAME_BY_PERIOD[p] for p in schedule.include_periods]
        explanation = f"{enumerate_with_and(periods)}, {explanation}"

    if schedule.exclude_periods:
        periods = [NAME_BY_PERIOD[p] for p in schedule.exclude_periods]
        explanation += f", sauf {enumerate_with_and(periods)}"

    return f"{explanation.capitalize()}."


if __name__ == '__main__':
    schedule = ScheduleItem(
        church_id=None,
        rrule='DTSTART:20240102T173000\nRRULE:FREQ=WEEKLY;BYDAY=TU,WE,TH,FR',
        exrule=None,
        duration_in_minutes=60,
        include_periods=[],
        exclude_periods=[PeriodEnum.JULY, PeriodEnum.AUGUST]
    )

    print(get_explanation_from_schedule(schedule))

    schedule = ScheduleItem(
        church_id=None,
        rrule='DTSTART:20240329T160000\nRRULE:FREQ=DAILY;UNTIL=20240329T170000',
        exrule=None,
        duration_in_minutes=60,
        include_periods=[PeriodEnum.LENT],
        exclude_periods=[]
    )

    print(get_explanation_from_schedule(schedule))

    schedule = ScheduleItem(
        church_id=None,
        rrule='DTSTART:20240105T210000\nRRULE:FREQ=MONTHLY;BYDAY=FR;BYSETPOS=1',
        exrule=None,
        duration_in_minutes=180,
        include_periods=[],
        exclude_periods=[]
    )

    print(get_explanation_from_schedule(schedule))
