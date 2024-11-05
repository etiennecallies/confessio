import unittest
from datetime import datetime

from scraping.parse.periods import PeriodEnum
from scraping.parse.rrule_utils import get_events_from_schedule_items
from scraping.parse.schedules import ScheduleItem, \
    RegularRule, Event


class GenerateEventsTests(unittest.TestCase):
    @staticmethod
    def get_fixtures():
        return [
            (
                [
                    ScheduleItem(
                        church_id=None,
                        date_rule=RegularRule(
                            rrule='DTSTART:20000101\nRRULE:FREQ=MONTHLY;BYDAY=1SA,3SA,5SA',
                            include_periods=[PeriodEnum.JANUARY, PeriodEnum.FEBRUARY],
                            exclude_periods=[]
                        ),
                        is_cancellation=False,
                        start_time_iso8601='16:00:00',
                        end_time_iso8601=None
                    )
                ],
                datetime(2024, 1, 1),
                datetime(2025, 1, 1),
                2024,
                [
                    datetime(2024, 1, 6, 16, 0),
                    datetime(2024, 1, 20, 16, 0),
                    datetime(2024, 2, 3, 16, 0),
                    datetime(2024, 2, 17, 16, 0),
                ]
            ),
        ]

    def test_generate_events(self):
        for schedules, start_datetime, end_datetime, default_year, expected_starts \
                in self.get_fixtures():
            with self.subTest():
                events = get_events_from_schedule_items(schedules,
                                                        start_datetime, end_datetime,
                                                        default_year)
                expected_events = [Event(church_id=None, start=start, end=None)
                                   for start in expected_starts]
                # print(explanation)
                self.assertListEqual(events, expected_events)


if __name__ == '__main__':
    unittest.main()
