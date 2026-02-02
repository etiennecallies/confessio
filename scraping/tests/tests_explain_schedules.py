import unittest

from scheduling.utils.date_utils import Weekday
from scheduling.workflows.parsing.explain_schedule import get_explanation_from_schedule
from scheduling.workflows.parsing.intervals import PeriodEnum
from scheduling.workflows.parsing.schedules import ScheduleItem, \
    RegularRule, OneOffRule, WeeklyRule, MonthlyRule, NWeekday, Position, CustomPeriod


class ExplainSchedulesTests(unittest.TestCase):
    @staticmethod
    def get_fixtures():
        return [
            (
                ScheduleItem(
                    church_id=None,
                    date_rule=RegularRule(
                        rule=WeeklyRule(
                            by_weekdays=[
                                Weekday.TUESDAY,
                                Weekday.WEDNESDAY,
                                Weekday.THURSDAY,
                                Weekday.FRIDAY
                            ]
                        ),
                        only_in_periods=[],
                        not_in_periods=[CustomPeriod(start=OneOffRule(day=1, month=7),
                                                     end=OneOffRule(day=31, month=8))],
                        not_on_dates=[],
                    ),
                    is_cancellation=False,
                    start_time_iso8601='17:30:00',
                    end_time_iso8601=None,
                ),
                'Toutes les semaines les mardi, mercredi, jeudi et vendredi à partir de 17:30, '
                'sauf du 1er juillet au 31 août.'
            ),
            (
                ScheduleItem(
                    church_id=None,
                    date_rule=OneOffRule(
                        year=None,
                        month=3,
                        day=29,
                        weekday=None,
                        liturgical_day=None,
                    ),
                    is_cancellation=False,
                    start_time_iso8601='17:30:00',
                    end_time_iso8601='18:00:00',
                ),
                'Le 29 mars de 17:30 à 18:00.'
            ),
            (
                ScheduleItem(
                    church_id=None,
                    date_rule=OneOffRule(
                        year=2024,
                        month=3,
                        day=29,
                        weekday=None,
                        liturgical_day=None,
                    ),
                    is_cancellation=False,
                    start_time_iso8601='17:30:00',
                    end_time_iso8601='18:00:00',
                ),
                'Le vendredi 29 mars 2024 de 17:30 à 18:00.'
            ),
            (
                ScheduleItem(
                    church_id=None,
                    date_rule=OneOffRule(
                        year=None,
                        month=3,
                        day=29,
                        weekday=Weekday.THURSDAY,
                        liturgical_day=None,
                    ),
                    is_cancellation=False,
                    start_time_iso8601='17:30:00',
                    end_time_iso8601='18:00:00',
                ),
                'Le jeudi 29 mars de 17:30 à 18:00.'
            ),
            (
                ScheduleItem(
                    church_id=None,
                    date_rule=RegularRule(
                        rule=MonthlyRule(
                            by_nweekdays=[
                                NWeekday(
                                    weekday=Weekday.FRIDAY,
                                    position=Position.FIRST,
                                )
                            ]
                        ),
                        only_in_periods=[],
                        not_in_periods=[],
                        not_on_dates=[],
                    ),
                    is_cancellation=False,
                    start_time_iso8601='21:00:00',
                    end_time_iso8601='00:00:00',
                ),
                'Le premier vendredi du mois de 21:00 à 00:00.'
            ),
            (
                ScheduleItem(
                    church_id=None,
                    date_rule=OneOffRule(
                        year=2023,
                        month=3,
                        day=26,
                        weekday=Weekday.THURSDAY,
                        liturgical_day=None
                    ),
                    is_cancellation=False,
                    start_time_iso8601='18:00:00',
                    end_time_iso8601=None,
                ),
                'Le jeudi 26 mars 2023 (⚠️ date impossible) à partir de 18:00.'
            ),
            (
                ScheduleItem(
                    church_id=None,
                    date_rule=RegularRule(
                        rule=MonthlyRule(
                            by_nweekdays=[
                                NWeekday(
                                    weekday=Weekday.SATURDAY,
                                    position=Position.FIRST,
                                ),
                                NWeekday(
                                    weekday=Weekday.SATURDAY,
                                    position=Position.THIRD,
                                ),
                                NWeekday(
                                    weekday=Weekday.SATURDAY,
                                    position=Position.FIFTH,
                                )
                            ]
                        ),
                        only_in_periods=[],
                        not_in_periods=[PeriodEnum.SCHOOL_HOLIDAYS],
                        not_on_dates=[],
                    ),
                    is_cancellation=False,
                    start_time_iso8601=None,
                    end_time_iso8601=None
                ),
                'Le premier samedi, le troisième samedi et le cinquième samedi du mois, '
                'sauf pendant les vacances scolaires.'
            ),
            (
                ScheduleItem(
                    church_id=None,
                    date_rule=RegularRule(
                        rule=WeeklyRule(
                            by_weekdays=[
                                Weekday.THURSDAY,
                            ]
                        ),
                        only_in_periods=[PeriodEnum.SUMMER],
                        not_in_periods=[],
                        not_on_dates=[],
                    ),
                    is_cancellation=False,
                    start_time_iso8601='17:30:00',
                    end_time_iso8601=None,
                ),
                'En été, toutes les semaines le jeudi à partir de 17:30.'
            ),
        ]

    def test_explain_schedules(self):
        for schedule, expected_explanation in self.get_fixtures():
            with self.subTest():
                explanation = get_explanation_from_schedule(schedule)
                # print(explanation)
                self.assertEqual(explanation, expected_explanation)


if __name__ == '__main__':
    unittest.main()
