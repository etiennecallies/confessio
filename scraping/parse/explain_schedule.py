from datetime import datetime

from home.utils.date_utils import format_datetime_with_locale, Weekday
from home.utils.list_utils import enumerate_with_and
from scraping.parse.periods import PeriodEnum, get_liturgical_date, LiturgicalDayEnum
from scraping.parse.schedules import (ScheduleItem, OneOffRule, RegularRule, Position,
                                      WeeklyRule, MonthlyRule)

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


def get_weekly_explanation(weekly_rule: WeeklyRule) -> str:
    prefix = "toutes les semaines"

    weekdays = [NAME_BY_WEEKDAY[w] for w in weekly_rule.by_weekdays]

    if not weekdays:
        raise ValueError("No weekday in weekly rrule")

    article = "le" if len(weekdays) == 1 else "les"

    return f"{prefix} {article} {enumerate_with_and(weekdays)}"


def get_daily_explanation() -> str:
    return "tous les jours"


def get_monthly_explanation(monthly_rule: MonthlyRule) -> str:
    if not monthly_rule.by_nweekdays:
        raise ValueError("No nweekday in monthly rule")

    items = []
    for nweekday in monthly_rule.by_nweekdays:
        items.append(f"le {NAME_BY_POSITION[nweekday.position]} "
                     f"{NAME_BY_WEEKDAY[nweekday.weekday]}")

    return f"{enumerate_with_and(items)} du mois"


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
        if one_off_rule.weekday:
            full_date += f"{NAME_BY_WEEKDAY[one_off_rule.weekday]} "
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
        if schedule.date_rule.is_weekly_rule():
            explanation += get_weekly_explanation(schedule.date_rule.rule)
        elif schedule.date_rule.is_daily_rule():
            explanation += get_daily_explanation()
        elif schedule.date_rule.is_monthly_rule():
            explanation += get_monthly_explanation(schedule.date_rule.rule)
        else:
            raise ValueError(f"Frequency not implemented yet")

    elif schedule.is_one_off_rule():
        explanation += get_one_off_explanation(schedule.date_rule)

    explanation += get_time_explanation(schedule)

    if schedule.is_regular_rule():
        if schedule.date_rule.only_in_periods:
            periods = [get_name_by_period(p) for p in schedule.date_rule.only_in_periods]
            explanation = f"{enumerate_with_and(periods)}, {explanation}"

        if schedule.date_rule.not_in_periods:
            periods = [get_name_by_period(p) for p in schedule.date_rule.not_in_periods]
            explanation += f", sauf {enumerate_with_and(periods)}"

        if schedule.date_rule.not_on_dates:
            not_on_dates = [get_one_off_explanation(d) for d in schedule.date_rule.not_on_dates]
            explanation += f", sauf {enumerate_with_and(not_on_dates)}"

    return f"{explanation.capitalize()}."


###########
# SORTING #
###########

def get_frequency_key(regular_rule: RegularRule) -> int:
    if regular_rule.is_daily_rule():
        return 0
    if regular_rule.is_weekly_rule():
        return 1
    if regular_rule.is_monthly_rule():
        return 2

    raise ValueError(f"Frequency not implemented yet")


POSITION_BY_WEEKDAY = {
    Weekday.MONDAY: 0,
    Weekday.TUESDAY: 1,
    Weekday.WEDNESDAY: 2,
    Weekday.THURSDAY: 3,
    Weekday.FRIDAY: 4,
    Weekday.SATURDAY: 5,
    Weekday.SUNDAY: 6,
}


def get_weekdays_key(regular_rule: RegularRule) -> tuple:
    if isinstance(regular_rule, WeeklyRule):
        return tuple(POSITION_BY_WEEKDAY[w] for w in regular_rule.by_weekdays)

    return tuple()


def regular_rule_sort_key(regular_rule: RegularRule) -> tuple:
    return (
        get_frequency_key(regular_rule),
        len(regular_rule.by_weekdays) if isinstance(regular_rule, WeeklyRule) else 0,
        get_weekdays_key(regular_rule),
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
