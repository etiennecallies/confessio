from scheduling.workflows.merging.sourced_schedules import SourcedScheduleItem
from scheduling.workflows.parsing.explain_schedule import schedule_item_sort_key


def sourced_schedule_item_sort_key(sourced_schedule_item: SourcedScheduleItem) -> tuple:
    return schedule_item_sort_key(sourced_schedule_item.item)


def get_sorted_sourced_schedule_items_by_church_id(sourced_schedule_items: list[SourcedScheduleItem]
                                                   ) -> dict[int, list[SourcedScheduleItem]]:
    sorted_schedules_by_church_id = {}

    for sourced_schedule_item in sorted(sourced_schedule_items, key=sourced_schedule_item_sort_key):
        sorted_schedules_by_church_id.setdefault(sourced_schedule_item.item.church_id, [])\
            .append(sourced_schedule_item)

    return sorted_schedules_by_church_id
