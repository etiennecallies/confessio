from typing import Callable

from scheduling.workflows.merging.sourced_schedule_items import SourcedScheduleItem
from scheduling.workflows.parsing.explain_schedule import get_explanation_from_schedule
from scheduling.workflows.parsing.liturgical import PeriodEnum
from scheduling.workflows.parsing.schedules import CustomPeriod, WeeklyRule


def get_periods_or_custom_periods_key(periods: list[PeriodEnum | CustomPeriod]) -> tuple:
    return (
        tuple(sorted(p for p in periods if isinstance(p, PeriodEnum))),
        tuple(sorted(p for p in periods if isinstance(p, CustomPeriod)))
    )


def merge_similar_weekly_rules_of_church(sourced_schedule_items: list[SourcedScheduleItem]
                                         ) -> list[SourcedScheduleItem]:
    results = []
    schedules_by_key = {}
    for sourced_schedule_item in sourced_schedule_items:
        date_rule = sourced_schedule_item.item.date_rule
        if not sourced_schedule_item.item.is_regular_rule() or \
                not date_rule.is_weekly_rule():
            results.append(sourced_schedule_item)
            continue

        key = (
            sourced_schedule_item.item.is_cancellation,
            sourced_schedule_item.item.start_time_iso8601,
            sourced_schedule_item.item.end_time_iso8601,
            get_periods_or_custom_periods_key(date_rule.only_in_periods),
            get_periods_or_custom_periods_key(date_rule.not_in_periods),
            tuple(sorted(date_rule.not_on_dates)),
        )
        schedules_by_key.setdefault(key, []).append(sourced_schedule_item)

    for schedules_group in schedules_by_key.values():
        first_schedule = schedules_group[0]
        if len(schedules_group) == 1:
            results.append(first_schedule)
            continue

        combined_weekdays_days = set()
        for sourced_schedule_item in schedules_group:
            combined_weekdays_days.update(
                sourced_schedule_item.item.date_rule.rule.by_weekdays)

        first_item = first_schedule.item
        combined_schedule_item = first_item.model_copy(
            update={
                'date_rule': first_item.date_rule.model_copy(
                    update={
                        'rule': WeeklyRule(by_weekdays=list(combined_weekdays_days))
                    }
                )
            }
        )

        sources = list(set(sum((cs.sources for cs in schedules_group), [])))
        combined_events = list(sorted(set(sum((cs.events for cs in schedules_group), []))))

        combined_parsing_schedule_item = SourcedScheduleItem(
            item=combined_schedule_item,
            explanation=get_explanation_from_schedule(combined_schedule_item),
            sources=sources,
            events=combined_events
        )

        results.append(combined_parsing_schedule_item)

    return results


def apply_on_same_church(
        sourced_schedule_items: list[SourcedScheduleItem],
        function_on_group: Callable[[list[SourcedScheduleItem]], list[SourcedScheduleItem]]
) -> list[SourcedScheduleItem]:
    sourced_schedule_items_by_church = {}
    for sourced_schedule_item in sourced_schedule_items:
        sourced_schedule_items_by_church.setdefault(
            sourced_schedule_item.item.church_id, []).append(sourced_schedule_item)

    sourced_schedule_items = []
    for sourced_schedule_items_group in sourced_schedule_items_by_church.values():
        sourced_schedule_items.extend(
            function_on_group(sourced_schedule_items_group)
        )

    return sourced_schedule_items


def eliminate_similar_with_unknow_church(sourced_schedule_items: list[SourcedScheduleItem]
                                         ) -> list[SourcedScheduleItem]:
    church_explanations = set()
    for sourced_schedule_item in sourced_schedule_items:
        if sourced_schedule_item.item.has_real_church():
            church_explanations.add(sourced_schedule_item.explanation)

    schedules_by_church_id_and_explanation = {}
    for sourced_schedule_item in sourced_schedule_items:
        if sourced_schedule_item.item.has_real_church() or \
                sourced_schedule_item.explanation not in church_explanations:
            # We ignore sourced_schedule_item with no church and with real-church explanation
            schedules_by_church_id_and_explanation.setdefault(
                (
                    sourced_schedule_item.item.church_id,
                    sourced_schedule_item.explanation,
                ), []).append(sourced_schedule_item)

    merged_schedules_items = []
    for schedules_group in schedules_by_church_id_and_explanation.values():
        sources = list(set(sum((cs.sources for cs in schedules_group), [])))
        merged_schedules_items.append(schedules_group[0].model_copy(update={'sources': sources}))

    return merged_schedules_items


def eliminate_similar_without_exception_of_church(sourced_schedule_items: list[SourcedScheduleItem]
                                                  ) -> list[SourcedScheduleItem]:
    explanations_dict = {}
    for sourced_schedule_item in sourced_schedule_items:
        item = sourced_schedule_item.item
        if item.is_one_off_rule():
            continue

        if item.date_rule.only_in_periods or \
                item.date_rule.not_in_periods or \
                item.date_rule.not_on_dates:
            schedule_item_without_exception = item.model_copy(
                update={
                    'date_rule': item.date_rule.model_copy(
                        update={
                            'only_in_periods': [],
                            'not_in_periods': [],
                            'not_on_dates': [],
                        }
                    )
                }
            )
            explanation_without_exceptions = get_explanation_from_schedule(
                schedule_item_without_exception)
            explanations_dict.setdefault(explanation_without_exceptions, [])\
                .append(sourced_schedule_item)

    results = []
    for sourced_schedule_item in sourced_schedule_items:
        item = sourced_schedule_item.item
        if item.is_one_off_rule():
            results.append(sourced_schedule_item)
            continue

        if not item.date_rule.only_in_periods and \
                not item.date_rule.not_in_periods and \
                not item.date_rule.not_on_dates:
            if sourced_schedule_item.explanation in explanations_dict \
                    and len(explanations_dict[sourced_schedule_item.explanation]) == 1:
                # We keep sourced_schedule_item with exception
                continue

        results.append(sourced_schedule_item)

    return results


def get_merged_sourced_schedule_items(sourced_schedule_items: list[SourcedScheduleItem]
                                      ) -> list[SourcedScheduleItem]:
    # First we merge weekly rules when possible
    sourced_schedule_items = apply_on_same_church(sourced_schedule_items,
                                                  merge_similar_weekly_rules_of_church)

    # Then we eliminate similar schedule_items with unknow church
    sourced_schedule_items = eliminate_similar_with_unknow_church(sourced_schedule_items)

    # Finally we eliminate similar schedule_items without exception
    sourced_schedule_items = apply_on_same_church(sourced_schedule_items,
                                                  eliminate_similar_without_exception_of_church)

    return sourced_schedule_items
