import unittest

from home.utils.date_utils import Weekday
from scraping.parse.schedules import OneOffRule


class SortSchedulesTests(unittest.TestCase):
    @staticmethod
    def get_fixtures():
        return [
            (
                OneOffRule(year=None, month=12, day=26, weekday=Weekday.FRIDAY),
                OneOffRule(year=2025, month=12, day=29, weekday=Weekday.MONDAY),
                OneOffRule(year=None, month=12, day=26, weekday=Weekday.FRIDAY),
            )
        ]

    def test_sort_schedules(self):
        for one_off_rule1, one_off_rule2, expected_first_one_off_rule in self.get_fixtures():
            with self.subTest():
                sorted_one_off_rules = sorted([one_off_rule2, one_off_rule1])
                first_one_off_rule = sorted_one_off_rules[0]
                # print(explanation)
                self.assertEqual(first_one_off_rule, expected_first_one_off_rule)


if __name__ == '__main__':
    unittest.main()
