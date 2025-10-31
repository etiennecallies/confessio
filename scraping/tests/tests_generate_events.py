import unittest
from datetime import datetime, date

from home.utils.date_utils import Weekday
from scraping.parse.holidays import HolidayZoneEnum
from scraping.parse.intervals import PeriodEnum
from scraping.parse.rrule_utils import get_events_from_schedule_items
from scraping.parse.schedules import ScheduleItem, \
    RegularRule, Event, MonthlyRule, NWeekday, Position, WeeklyRule, CustomPeriod, OneOffRule


class GenerateEventsTests(unittest.TestCase):
    @staticmethod
    def get_fixtures():
        return [
            (
                [
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
                            only_in_periods=[CustomPeriod(
                                start=OneOffRule(day=1, month=1),
                                end=OneOffRule(day=28, month=2))],
                            not_in_periods=[],
                            not_on_dates=[],
                        ),
                        is_cancellation=False,
                        start_time_iso8601='16:00:00',
                        end_time_iso8601=None
                    )
                ],
                date(2024, 1, 1),
                date(2025, 1, 1),
                2024,
                [
                    datetime(2024, 1, 6, 16, 0),
                    datetime(2024, 1, 20, 16, 0),
                    datetime(2024, 2, 3, 16, 0),
                    datetime(2024, 2, 17, 16, 0),
                ]
            ),
            (
                [
                    ScheduleItem(
                        church_id=None,
                        date_rule=RegularRule(
                            rule=WeeklyRule(
                                by_weekdays=[
                                    Weekday.FRIDAY
                                ]
                            ),
                            only_in_periods=[],
                            not_in_periods=[],
                            not_on_dates=[],
                        ),
                        is_cancellation=False,
                        start_time_iso8601='17:00:00',
                        end_time_iso8601=None
                    )
                ],
                date(2024, 1, 1),
                date(2024, 1, 8),
                2024,
                [
                    datetime(2024, 1, 5, 17, 0),
                ]
            ),
            (
                [
                    ScheduleItem(
                        church_id=None,
                        date_rule=RegularRule(
                            rule=WeeklyRule(
                                by_weekdays=[
                                    Weekday.TUESDAY,
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
                ],
                date(2024, 1, 1),
                date(2024, 12, 31),
                2024,
                [
                    datetime(2024, 7, 2, 17, 30),
                    datetime(2024, 7, 9, 17, 30),
                    datetime(2024, 7, 16, 17, 30),
                    datetime(2024, 7, 23, 17, 30),
                    datetime(2024, 7, 30, 17, 30),
                    datetime(2024, 8, 6, 17, 30),
                    datetime(2024, 8, 13, 17, 30),
                    datetime(2024, 8, 20, 17, 30),
                    datetime(2024, 8, 27, 17, 30),
                ]
            ),
        ]

    def test_generate_events(self):
        for schedules, start_date, end_date, default_year, expected_starts \
                in self.get_fixtures():
            with self.subTest():
                events = get_events_from_schedule_items(schedules,
                                                        start_date,
                                                        default_year,
                                                        HolidayZoneEnum.FR_ZONE_A,
                                                        end_date)
                expected_events = [Event(church_id=None, start=start, end=None)
                                   for start in expected_starts]
                # print(explanation)
                self.assertListEqual(events, expected_events)


if __name__ == '__main__':
    unittest.main()
