from fetching.models import OClocherMatching, OClocherSchedule, OClocherMatchingModeration
from fetching.public_service import fetching_get_matching_matrix
from fetching.services.oclocher_moderations_service import upsert_matching_moderation
from scheduling.utils.date_utils import datetime_in_timezone
from scheduling.workflows.parsing.schedules import ScheduleItem, SchedulesList, OneOffRule


def get_schedule_item_from_oclocher_schedule(oclocher_schedule: OClocherSchedule,
                                             church_id_by_oclocher_id: dict[str, int],
                                             timezone_str: str,
                                             ) -> ScheduleItem:
    datetime_start = datetime_in_timezone(oclocher_schedule.datetime_start, timezone_str)
    datetime_end = datetime_in_timezone(oclocher_schedule.datetime_end, timezone_str) \
        if oclocher_schedule.datetime_end else None

    return ScheduleItem(
        church_id=church_id_by_oclocher_id.get(oclocher_schedule.location.location_id, -1),
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
    if not matching_matrix:
        print(f'No matching matrix for OClocherMatching for this reason'
              f' {oclocher_matching.llm_error_detail}')
        return SchedulesList(schedules=[])

    church_id_by_oclocher_id = {}
    for location_church_mapping in matching_matrix.mappings:
        church_id = location_church_mapping.church_id
        location_id = location_church_mapping.location_id
        if church_id is None:
            continue

        church_id_by_oclocher_id[oclocher_id_by_location_id[location_id]] = church_id

    schedules = [
        get_schedule_item_from_oclocher_schedule(oclocher_schedule, church_id_by_oclocher_id,
                                                 timezone_str)
        for oclocher_schedule in oclocher_schedules
    ]

    if any(not s.has_real_church() for s in schedules):
        one_schedule = oclocher_schedules[0]
        oclocher_organization = one_schedule.organization
        upsert_matching_moderation(oclocher_organization, oclocher_matching,
                                   OClocherMatchingModeration.Category.CHURCHES_MISSING,
                                   moderation_validated=False,
                                   )

    return SchedulesList(
        schedules=schedules,
    )
