from dataclasses import dataclass

from scheduling.models import Parsing
from scheduling.models import Scheduling, IndexEvent
from scheduling.public_model import SourcedSchedulesList
from scheduling.services.merging.index_events_service import \
    build_sourced_schedules_and_index_events
from scheduling.services.merging.sourced_schedules_service import build_scheduling_elements
from scheduling.services.parsing.parse_pruning_service import remove_useless_moderation_for_parsing
from scheduling.services.scheduling.scheduling_service import build_resources_hash


@dataclass
class SchedulingIndexingObjects:
    sourced_schedules_list: SourcedSchedulesList
    church_uuid_by_id: dict[int, str]
    index_events: list[IndexEvent]
    resources_hash: str


def do_index_scheduling(scheduling: Scheduling) -> SchedulingIndexingObjects:
    # Build scheduling elements
    scheduling_elements = build_scheduling_elements(scheduling.website, scheduling)

    church_uuid_by_id = {church_id: str(church.uuid) for church_id, church
                         in scheduling_elements.church_by_id.items()}

    # Build index events
    index_events = build_sourced_schedules_and_index_events(scheduling.website, scheduling,
                                                            scheduling_elements)

    # We build the resources hash to avoid doing it inside the transaction
    resources_hash = build_resources_hash(scheduling, scheduling_elements.sourced_schedules_list,
                                          church_uuid_by_id, index_events)

    return SchedulingIndexingObjects(
        sourced_schedules_list=scheduling_elements.sourced_schedules_list,
        church_uuid_by_id=church_uuid_by_id,
        index_events=index_events,
        resources_hash=resources_hash,
    )


def clean_parsings_moderations(parsing_history_ids: list[int]):
    for parsing_history_id in parsing_history_ids:
        historical_parsing = Parsing.history.get(history_id=parsing_history_id)
        parsing = historical_parsing.instance
        remove_useless_moderation_for_parsing(parsing)
