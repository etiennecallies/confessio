from fetching.models import OClocherMatching, OClocherSchedule
from fetching.public_service import fetching_get_matching_matrix
from scheduling.workflows.parsing.schedules import ScheduleItem, SchedulesList, OneOffRule


def get_schedule_item_from_oclocher_schedule(oclocher_schedule: OClocherSchedule,
                                             church_id_by_oclocher_id: dict[str, int],
                                             ) -> ScheduleItem | None:
    if oclocher_schedule.location.location_id not in church_id_by_oclocher_id:
        return None

    return ScheduleItem(
        church_id=church_id_by_oclocher_id[oclocher_schedule.location.location_id],
        date_rule=OneOffRule(
            year=oclocher_schedule.datetime_start.year,
            month=oclocher_schedule.datetime_start.month,
            day=oclocher_schedule.datetime_start.day,
        ),
        start_time_iso8601=str(oclocher_schedule.datetime_start.time()),
        end_time_iso8601=str(oclocher_schedule.datetime_end.time())
        if oclocher_schedule.datetime_end else None,
    )


def get_schedules_list_from_oclocher_schedules(oclocher_schedules: list[OClocherSchedule],
                                               oclocher_matching: OClocherMatching,
                                               oclocher_id_by_location_id: dict[int, str],
                                               ) -> SchedulesList:
    matching_matrix = fetching_get_matching_matrix(oclocher_matching)

    church_id_by_oclocher_id = {}
    for mapping in matching_matrix.mappings:
        church_id = mapping[0]
        location_id = mapping[1]
        church_id_by_oclocher_id[oclocher_id_by_location_id[location_id]] = church_id

    schedules = [
        get_schedule_item_from_oclocher_schedule(oclocher_schedule, church_id_by_oclocher_id)
        for oclocher_schedule in oclocher_schedules
    ]

    return SchedulesList(
        schedules=[s for s in schedules if s is not None],
    )
