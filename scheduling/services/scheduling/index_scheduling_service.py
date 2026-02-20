from scheduling.models import Parsing
from scheduling.models import Scheduling, IndexEvent
from scheduling.services.merging.index_events_service import \
    build_sourced_schedules_and_index_events
from scheduling.services.parsing.parse_pruning_service import remove_useless_moderation_for_parsing


def do_index_scheduling(scheduling: Scheduling) -> list[IndexEvent]:
    return build_sourced_schedules_and_index_events(scheduling.website, scheduling)


def clean_parsings_moderations(parsing_history_ids: list[int]):
    for parsing_history_id in parsing_history_ids:
        historical_parsing = Parsing.history.get(history_id=parsing_history_id)
        parsing = historical_parsing.instance
        remove_useless_moderation_for_parsing(parsing)
