from scheduling.utils.date_utils import Weekday
from scheduling.workflows.parsing.liturgical import PeriodEnum
from scheduling.workflows.parsing.schedules import SchedulesList, CustomPeriod, OneOffRule, \
    ScheduleItem, RegularRule, DailyRule, WeeklyRule, MonthlyRule, sort_periods


def convert_legacy_period_enum(period_as_dict: dict) -> PeriodEnum | CustomPeriod:
    if 'start' in period_as_dict:
        return CustomPeriod(
            start=OneOffRule(**period_as_dict['start']),
            end=OneOffRule(**period_as_dict['end'])
        )

    return PeriodEnum(period_as_dict)


def convert_legacy_rule(rule_as_dict: dict) -> DailyRule | WeeklyRule | MonthlyRule:
    if 'by_weekdays' in rule_as_dict:
        return WeeklyRule(by_weekdays=list(sorted([Weekday(w)
                                                   for w in rule_as_dict['by_weekdays']])))

    if 'by_nweekdays' in rule_as_dict:
        return MonthlyRule(by_nweekdays=rule_as_dict['by_nweekdays'])

    return DailyRule()


def convert_date_rule(date_rule_json: dict) -> OneOffRule | RegularRule:
    if 'rule' in date_rule_json:
        return RegularRule(
            rule=convert_legacy_rule(date_rule_json['rule']),
            only_in_periods=sort_periods([convert_legacy_period_enum(p)
                                          for p in date_rule_json['only_in_periods']]),
            not_in_periods=sort_periods([convert_legacy_period_enum(p)
                                         for p in date_rule_json['not_in_periods']]),
            not_on_dates=list(sorted([OneOffRule(**d) for d in date_rule_json['not_on_dates']])),
        )

    return OneOffRule(**date_rule_json)


def convert_legacy_schedules(schedules_json: dict) -> list[ScheduleItem]:
    return [
        ScheduleItem(
            church_id=d['church_id'],
            date_rule=convert_date_rule(d['date_rule']),
            is_cancellation=d['is_cancellation'],
            start_time_iso8601=d['start_time_iso8601'],
            end_time_iso8601=d['end_time_iso8601'],
        ) for d in schedules_json
    ]


def from_v1_1_to_v1_2(schedules_list_json: dict) -> SchedulesList:
    return SchedulesList(
        schedules=convert_legacy_schedules(schedules_list_json['schedules']),
        possible_by_appointment=schedules_list_json['possible_by_appointment'],
        is_related_to_mass=schedules_list_json['is_related_to_mass'],
        is_related_to_adoration=schedules_list_json['is_related_to_adoration'],
        is_related_to_permanence=schedules_list_json['is_related_to_permanence'],
        will_be_seasonal_events=schedules_list_json['will_be_seasonal_events'],
    )
