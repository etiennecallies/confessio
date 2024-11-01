import unittest

from scraping.parse.explain_schedule import get_explanation_from_schedule
from scraping.parse.periods import PeriodEnum
from scraping.parse.schedules import ScheduleItem, \
    RegularRule, OneOffRule


class ExplainSchedulesTests(unittest.TestCase):
    @staticmethod
    def get_fixtures():
        return [
            (
                ScheduleItem(
                    church_id=None,
                    date_rule=RegularRule(
                        rrule='DTSTART:20240102\nRRULE:FREQ=WEEKLY;BYDAY=TU,WE,TH,FR',
                        include_periods=[],
                        exclude_periods=[PeriodEnum.JULY, PeriodEnum.AUGUST]
                    ),
                    is_cancellation=False,
                    start_time_iso8601='17:30:00',
                    end_time_iso8601=None,
                ),
                'Toutes les semaines les mardi, mercredi, jeudi et vendredi à partir de 17:30, '
                'sauf en juillet et en août.'
            ),
            (
                ScheduleItem(
                    church_id=None,
                    date_rule=OneOffRule(
                        year=None,
                        month=3,
                        day=29,
                        weekday_iso8601=None,
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
                        weekday_iso8601=None,
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
                        weekday_iso8601=4,
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
                        rrule='DTSTART:20240105T210000\nRRULE:FREQ=MONTHLY;BYDAY=FR;BYSETPOS=1',
                        include_periods=[],
                        exclude_periods=[]
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
                    date_rule=RegularRule(
                        rrule='DTSTART:20240616T160000\nRRULE:FREQ=MONTHLY;BYMONTHDAY=16',
                        include_periods=[],
                        exclude_periods=[]
                    ),
                    is_cancellation=False,
                    start_time_iso8601='16:00:00',
                    end_time_iso8601='19:00:00',
                ),
                'Le 16 du mois de 16:00 à 19:00.'
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
