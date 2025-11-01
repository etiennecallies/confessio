from scraping.parse.liturgical import PeriodEnum
from scraping.parse.schedules import SchedulesList, CustomPeriod, OneOffRule, ScheduleItem, \
    RegularRule


def convert_legacy_period_enum(period_as_str: str) -> PeriodEnum | CustomPeriod:
    if period_as_str == 'january':
        return CustomPeriod(start=OneOffRule(month=1, day=1),
                            end=OneOffRule(month=1, day=31))
    if period_as_str == 'february':
        return CustomPeriod(start=OneOffRule(month=2, day=1),
                            end=OneOffRule(month=2, day=28))  # ignore leap year
    if period_as_str == 'march':
        return CustomPeriod(start=OneOffRule(month=3, day=1),
                            end=OneOffRule(month=3, day=31))
    if period_as_str == 'april':
        return CustomPeriod(start=OneOffRule(month=4, day=1),
                            end=OneOffRule(month=4, day=30))
    if period_as_str == 'may':
        return CustomPeriod(start=OneOffRule(month=5, day=1),
                            end=OneOffRule(month=5, day=31))
    if period_as_str == 'june':
        return CustomPeriod(start=OneOffRule(month=6, day=1),
                            end=OneOffRule(month=6, day=30))
    if period_as_str == 'july':
        return CustomPeriod(start=OneOffRule(month=7, day=1),
                            end=OneOffRule(month=7, day=31))
    if period_as_str == 'august':
        return CustomPeriod(start=OneOffRule(month=8, day=1),
                            end=OneOffRule(month=8, day=31))
    if period_as_str == 'september':
        return CustomPeriod(start=OneOffRule(month=9, day=1),
                            end=OneOffRule(month=9, day=30))
    if period_as_str == 'october':
        return CustomPeriod(start=OneOffRule(month=10, day=1),
                            end=OneOffRule(month=10, day=31))
    if period_as_str == 'november':
        return CustomPeriod(start=OneOffRule(month=11, day=1),
                            end=OneOffRule(month=11, day=30))
    if period_as_str == 'december':
        return CustomPeriod(start=OneOffRule(month=12, day=1),
                            end=OneOffRule(month=12, day=31))

    return PeriodEnum(period_as_str)


def convert_date_rule(date_rule_json: dict) -> OneOffRule | RegularRule:
    if 'rule' in date_rule_json:
        return RegularRule(
            rule=date_rule_json['rule'],
            only_in_periods=[convert_legacy_period_enum(p)
                             for p in date_rule_json['only_in_periods']],
            not_in_periods=[convert_legacy_period_enum(p)
                            for p in date_rule_json['not_in_periods']],
            not_on_dates=date_rule_json['not_on_dates']
        )

    return OneOffRule(**date_rule_json)


def convert_legacy_schedules(schedules_json: dict) -> list[ScheduleItem]:
    return [
        ScheduleItem(
            church_id=d['church_id'],
            date_rule=d['date_rule'],
            is_cancellation=d['is_cancellation'],
            start_time_iso8601=d['start_time_iso8601'],
            end_time_iso8601=d['end_time_iso8601'],
        ) for d in schedules_json
    ]


def from_v1_0_to_v1_1(schedules_list_json: dict) -> SchedulesList:
    return SchedulesList(
        schedules=convert_legacy_schedules(schedules_list_json['schedules']),
        possible_by_appointment=schedules_list_json['possible_by_appointment'],
        is_related_to_mass=schedules_list_json['is_related_to_mass'],
        is_related_to_adoration=schedules_list_json['is_related_to_adoration'],
        is_related_to_permanence=schedules_list_json['is_related_to_permanence'],
        will_be_seasonal_events=schedules_list_json['will_be_seasonal_events'],
    )
