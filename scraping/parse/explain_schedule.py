from datetime import datetime
from enum import Enum

from dateutil.rrule import rrulestr, rrule

from home.utils.date_utils import format_datetime_with_locale
from home.utils.list_utils import enumerate_with_and
from scraping.parse.periods import PeriodEnum, get_liturgical_date, LiturgicalDayEnum
from scraping.parse.schedules import ScheduleItem, OneOffRule, RegularRule


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

NAME_BY_LITURGICAL_DAY = {
    LiturgicalDayEnum.ASH_WEDNESDAY: "mercredi des Cendres",
    LiturgicalDayEnum.PALM_SUNDAY: "dimanche des Rameaux",
    LiturgicalDayEnum.HOLY_MONDAY: "lundi Saint",
    LiturgicalDayEnum.HOLY_TUESDAY: "mardi Saint",
    LiturgicalDayEnum.HOLY_WEDNESDAY: "mercredi Saint",
    LiturgicalDayEnum.MAUNDY_THURSDAY: "jeudi Saint",
    LiturgicalDayEnum.GOOD_FRIDAY: "vendredi Saint",
    LiturgicalDayEnum.HOLY_SATURDAY: "samedi Saint",
    LiturgicalDayEnum.EASTER_SUNDAY: "dimanche de Pâques",
    LiturgicalDayEnum.ASCENSION: "jeudi de l'Ascension",
    LiturgicalDayEnum.PENTECOST: "dimanche de Pentecôte",
}

PERIOD_BY_MONTH = {
    1: PeriodEnum.JANUARY,
    2: PeriodEnum.FEBRUARY,
    3: PeriodEnum.MARCH,
    4: PeriodEnum.APRIL,
    5: PeriodEnum.MAY,
    6: PeriodEnum.JUNE,
    7: PeriodEnum.JULY,
    8: PeriodEnum.AUGUST,
    9: PeriodEnum.SEPTEMBER,
    10: PeriodEnum.OCTOBER,
    11: PeriodEnum.NOVEMBER,
    12: PeriodEnum.DECEMBER,
}

NAME_BY_MONTH = {
    PeriodEnum.JANUARY: 'janvier',
    PeriodEnum.FEBRUARY: 'février',
    PeriodEnum.MARCH: 'mars',
    PeriodEnum.APRIL: 'avril',
    PeriodEnum.MAY: 'mai',
    PeriodEnum.JUNE: 'juin',
    PeriodEnum.JULY: 'juillet',
    PeriodEnum.AUGUST: 'août',
    PeriodEnum.SEPTEMBER: 'septembre',
    PeriodEnum.OCTOBER: 'octobre',
    PeriodEnum.NOVEMBER: 'novembre',
    PeriodEnum.DECEMBER: 'décembre',
}


def get_name_by_period(period: PeriodEnum) -> str:
    if period == PeriodEnum.ADVENT:
        return 'pendant l\'avent'
    if period == PeriodEnum.LENT:
        return 'pendant le carême'
    if period == PeriodEnum.SCHOOL_HOLIDAYS:
        return 'pendant les vacances scolaires'

    return f'en {NAME_BY_MONTH[period]}'


def get_weekly_explanation(rstr: rrule) -> str:
    prefix = "toutes les semaines"

    weekdays = [NAME_BY_WEEKDAY[Weekday(w)] for w in rstr._byweekday]

    if not weekdays:
        raise ValueError("No weekday in weekly rrule")

    article = "le" if len(weekdays) == 1 else "les"

    return f"{prefix} {article} {enumerate_with_and(weekdays)}"


def get_daily_explanation(rstr: rrule) -> str:
    if rstr._until:
        raise ValueError("Until date in daily rrule not implemented yet")

    return "tous les jours"


def get_monthly_explanation(rstr: rrule) -> str:
    if rstr._bymonthday:
        if len(rstr._bymonthday) > 1:
            raise ValueError("Multiple month days in monthly rrule not implemented yet")

        return f"le {rstr._bymonthday[0]} du mois"

    if rstr._bynweekday:
        items = []
        for weekday, position in rstr._bynweekday:
            if position == 0:
                raise ValueError("Position 0 in monthly rrule not implemented yet")

            items.append(f"le {NAME_BY_POSITION[Position(position)]} "
                         f"{NAME_BY_WEEKDAY[Weekday(weekday)]}")

        return f"{enumerate_with_and(items)} du mois"

    if not rstr._byweekday:
        raise ValueError("No weekday in monthly rrule")
    by_days = [Weekday(w) for w in rstr._byweekday]

    if len(by_days) > 1:
        raise ValueError("Multiple weekdays in monthly rrule not implemented yet")

    if not rstr._bysetpos:
        raise ValueError("No set position in monthly rrule")
    by_set_positions = [NAME_BY_POSITION[Position(p)] for p in rstr._bysetpos]

    article = "le" if len(by_set_positions) == 1 else "les"

    return f"{article} {enumerate_with_and(by_set_positions)} {NAME_BY_WEEKDAY[by_days[0]]} du mois"


def get_one_off_explanation(one_off_rule: OneOffRule) -> str:
    if one_off_rule.year and one_off_rule.is_valid_date():
        if one_off_rule.liturgical_day:
            dt_start = get_liturgical_date(one_off_rule.liturgical_day, one_off_rule.year)
        else:
            dt_start = datetime(one_off_rule.year,
                                one_off_rule.month,
                                one_off_rule.day)
        full_date = format_datetime_with_locale(dt_start, "%A %d %B %Y",
                                                'fr_FR.UTF-8')
    elif one_off_rule.liturgical_day:
        full_date = NAME_BY_LITURGICAL_DAY[one_off_rule.liturgical_day]
    else:
        full_date = ''
        if one_off_rule.weekday_iso8601:
            weekday_python = one_off_rule.weekday_iso8601 - 1
            full_date += f"{NAME_BY_WEEKDAY[Weekday(weekday_python)]} "
        full_date += f"{one_off_rule.day} {NAME_BY_MONTH[PERIOD_BY_MONTH[one_off_rule.month]]}"
        if one_off_rule.year:
            full_date += f" {one_off_rule.year} (⚠️ date impossible)"

    return f"le {full_date.lower()}"


def get_time_explanation(schedule: ScheduleItem) -> str:
    explanation = ''

    start_time = schedule.get_start_time()
    start_time_str = start_time.strftime('%H:%M') if start_time is not None else '00:00'
    if start_time_str != '00:00':
        end_time = schedule.get_end_time()
        if end_time is not None:
            end_time_str = end_time.strftime('%H:%M')
            explanation += f" de {start_time_str} à {end_time_str}"
        else:
            explanation += f" à partir de {start_time_str}"

    return explanation


def get_explanation_from_schedule(schedule: ScheduleItem) -> str:
    explanation = ''

    if schedule.is_cancellation:
        explanation += "pas de confessions "

    if schedule.is_regular_rule():
        rstr = rrulestr(schedule.date_rule.rrule)

        if not rstr._dtstart:
            raise ValueError("No start date in rrule")

        frequency = Frequency(rstr._freq)
        if frequency == Frequency.WEEKLY or (frequency == Frequency.DAILY and rstr._byweekday):
            explanation += get_weekly_explanation(rstr)
        elif frequency == Frequency.DAILY:
            explanation += get_daily_explanation(rstr)
        elif frequency == Frequency.MONTHLY:
            explanation += get_monthly_explanation(rstr)
        else:
            raise ValueError(f"Frequency {frequency} not implemented yet")

    elif schedule.is_one_off_rule():
        explanation += get_one_off_explanation(schedule.date_rule)

    explanation += get_time_explanation(schedule)

    if schedule.is_regular_rule():
        if schedule.date_rule.include_periods:
            periods = [get_name_by_period(p) for p in schedule.date_rule.include_periods]
            explanation = f"{enumerate_with_and(periods)}, {explanation}"

        if schedule.date_rule.exclude_periods:
            periods = [get_name_by_period(p) for p in schedule.date_rule.exclude_periods]
            explanation += f", sauf {enumerate_with_and(periods)}"

    return f"{explanation.capitalize()}."


###########
# SORTING #
###########

def regular_rule_sort_key(regular_rule: RegularRule) -> tuple:
    rstr = rrulestr(regular_rule.rrule)
    return (
        Frequency(rstr._freq).value,
        len(rstr._byweekday) if rstr._byweekday else 0,
        tuple(Weekday(w).value for w in rstr._byweekday) if rstr._byweekday else (),
    )


def one_off_rule_sort_key(one_off_rule: OneOffRule) -> tuple:
    # Sort by year, month, day
    return (
        one_off_rule.year or 0,
        one_off_rule.month or 0,
        one_off_rule.day or 0
    )


def schedule_item_sort_key(item: ScheduleItem) -> tuple:
    return (
        item.is_cancellation,  # Cancellation items come last (False < True).
        item.is_one_off_rule(),  # RegularRule comes first (False < True).
        (
            regular_rule_sort_key(item.date_rule) if item.is_regular_rule()
            else one_off_rule_sort_key(item.date_rule)
        ),
        item.start_time_iso8601 or '',  # Sort by start time.
        item.end_time_iso8601 or '',  # Sort by end time.
    )


def sort_schedules(schedules: list[ScheduleItem]) -> list[ScheduleItem]:
    return sorted(list(set(schedules)), key=schedule_item_sort_key)


################
# EXPLANATIONS #
################

def get_sorted_schedules_by_church_id(schedules: list[ScheduleItem]
                                      ) -> dict[int, list[ScheduleItem]]:
    sorted_schedules_by_church_id = {}

    for schedule in sort_schedules(schedules):
        sorted_schedules_by_church_id.setdefault(schedule.church_id, [])\
            .append(schedule)

    return sorted_schedules_by_church_id
