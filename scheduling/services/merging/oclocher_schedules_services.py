from fetching.models import OClocherMatching, OClocherSchedule, OClocherMatchingModeration
from fetching.public_service import fetching_get_matching_matrix
from fetching.services.oclocher_moderations_service import upsert_matching_moderation
from scheduling.utils.date_utils import datetime_in_timezone
from scheduling.workflows.parsing.schedules import ScheduleItem, SchedulesList, OneOffRule


def get_schedule_item_from_oclocher_schedule(oclocher_schedule: OClocherSchedule,
                                             church_id_by_oclocher_id: dict[str, int],
                                             timezone_str: str,
                                             ) -> ScheduleItem | None:
    if oclocher_schedule.location.location_id not in church_id_by_oclocher_id:
        return None

    datetime_start = datetime_in_timezone(oclocher_schedule.datetime_start, timezone_str)
    datetime_end = datetime_in_timezone(oclocher_schedule.datetime_end, timezone_str) \
        if oclocher_schedule.datetime_end else None

    return ScheduleItem(
        church_id=church_id_by_oclocher_id[oclocher_schedule.location.location_id],
        date_rule=OneOffRule(
            year=datetime_start.year,
            month=datetime_start.month,
            day=datetime_start.day,
        ),
        start_time_iso8601=str(datetime_start.time()),
        end_time_iso8601=str(datetime_end.time()) if datetime_end else None,
    )


def get_schedules_list_from_oclocher_schedules(oclocher_schedules: list[OClocherSchedule],
                                               oclocher_matching: OClocherMatching,
                                               oclocher_id_by_location_id: dict[int, str],
                                               timezone_str: str,
                                               ) -> SchedulesList:
    assert oclocher_schedules

    matching_matrix = fetching_get_matching_matrix(oclocher_matching)

    church_id_by_oclocher_id = {}
    for mapping in matching_matrix.mappings:
        church_id = mapping[0]
        location_id = mapping[1]
        church_id_by_oclocher_id[oclocher_id_by_location_id[location_id]] = church_id

    schedules = [
        get_schedule_item_from_oclocher_schedule(oclocher_schedule, church_id_by_oclocher_id,
                                                 timezone_str)
        for oclocher_schedule in oclocher_schedules
    ]

    if any(s is None for s in schedules):
        one_schedule = oclocher_schedules[0]
        oclocher_organization = one_schedule.organization
        upsert_matching_moderation(oclocher_organization, oclocher_matching,
                                   OClocherMatchingModeration.Category.CHURCHES_MISSING,
                                   moderation_validated=False,
                                   )

    return SchedulesList(
        schedules=[s for s in schedules if s is not None],
    )
