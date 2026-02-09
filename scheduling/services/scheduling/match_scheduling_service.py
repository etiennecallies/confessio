from dataclasses import dataclass

from fetching.models import OClocherLocation
from fetching.public_service import fetching_match_churches_and_locations
from registry.models import Church
from scheduling.models import Scheduling, SchedulingHistoricalOClocherMatching


@dataclass
class SchedulingMatchingObjects:
    oclocher_matching_history_ids: list[int]


def do_match_scheduling(scheduling: Scheduling) -> SchedulingMatchingObjects:
    locations = []
    for scheduling_historical_location in scheduling.historical_oclocher_locations.all():
        location_history_id = scheduling_historical_location.oclocher_location_history_id
        historical_location = OClocherLocation.history.get(history_id=location_history_id)
        locations.append(historical_location.instance)

    if not locations:
        return SchedulingMatchingObjects(
            oclocher_matching_history_ids=[],
        )

    churches = []
    for scheduling_historical_church in scheduling.historical_churches.all():
        church_history_id = scheduling_historical_church.church_history_id
        historical_church = Church.history.get(history_id=church_history_id)
        churches.append(historical_church.instance)

    if not churches:
        return SchedulingMatchingObjects(
            oclocher_matching_history_ids=[],
        )

    oclocher_matching = fetching_match_churches_and_locations(churches, locations)
    oclocher_matching_history_id = oclocher_matching.history.latest().history_id

    return SchedulingMatchingObjects(
        oclocher_matching_history_ids=[oclocher_matching_history_id],
    )


def bulk_create_scheduling_matching_objects(
        scheduling: Scheduling,
        scheduling_matching_objects: SchedulingMatchingObjects):
    # SchedulingHistoricalOClocherMatching
    oclocher_matching_objs = [
        SchedulingHistoricalOClocherMatching(
            scheduling=scheduling,
            oclocher_matching_history_id=matching_id
        ) for matching_id in scheduling_matching_objects.oclocher_matching_history_ids
    ]
    SchedulingHistoricalOClocherMatching.objects.bulk_create(oclocher_matching_objs)
