from dataclasses import dataclass

from home.models import Pruning
from scheduling.models import Scheduling, PruningParsing
from scraping.services.parse_pruning_service import do_parse_pruning_for_website


@dataclass
class SchedulingParsingObjects:
    pruning_parsing_history_ids: list[tuple[int, int]]


def do_parse_scheduling(scheduling: Scheduling) -> SchedulingParsingObjects:
    all_pruning_history_ids = []
    for scraping_pruning in scheduling.scraping_prunings.all():
        all_pruning_history_ids.append(scraping_pruning.pruning_history_id)

    for image_pruning in scheduling.image_prunings.all():
        all_pruning_history_ids.append(image_pruning.pruning_history_id)

    pruning_parsing_history_ids = []
    for pruning_history_id in all_pruning_history_ids:
        historical_pruning = Pruning.history.get(history_id=pruning_history_id)
        pruning = historical_pruning.instance

        # TODO force parsing with church list
        do_parse_pruning_for_website(pruning, scheduling.website)

        parsing = pruning.get_parsing(scheduling.website)
        if parsing is None:
            continue

        parsing_history_id = parsing.history.latest().history_id
        pruning_parsing_history_ids.append((pruning_history_id, parsing_history_id))

    return SchedulingParsingObjects(
        pruning_parsing_history_ids=pruning_parsing_history_ids,
    )


def bulk_create_scheduling_parsing_objects(
        scheduling: Scheduling,
        scheduling_parsing_objects: SchedulingParsingObjects):
    # PruningParsing
    parsing_objs = [
        PruningParsing(
            scheduling=scheduling,
            pruning_history_id=pruning_history_id,
            parsing_history_id=parsing_history_id,
        ) for pruning_history_id, parsing_history_id
        in scheduling_parsing_objects.pruning_parsing_history_ids
    ]
    PruningParsing.objects.bulk_create(parsing_objs)
