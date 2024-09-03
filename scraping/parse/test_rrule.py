from datetime import datetime

from dateutil.rrule import rrule, rruleset, WEEKLY, DAILY

if __name__ == '__main__':
    # Create an rruleset
    rules = rruleset()

    # Rule: Every Wednesday
    weekly_rule = rrule(WEEKLY, dtstart=datetime(2024, 1, 1, 10, 30),
                        byweekday=2)  # Every Wednesday
    rules.rrule(weekly_rule)
    print(str(weekly_rule))

    # Exclusion Rule: Nothing in August
    # Exclude every day in August
    august_exrule = rrule(DAILY, dtstart=datetime(2024, 8, 1),
                          until=datetime(2024, 8, 31))
    rules.exrule(august_exrule)
    print(str(august_exrule))

    # Print occurrences between two dates
    for occurrence in rules.between(datetime(2024, 1, 1),
                                    datetime(2024, 12, 31)):
        print(occurrence)
