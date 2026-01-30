from dataclasses import dataclass

from home.models import Church
from scheduling.models import Scheduling, PruningParsing
from scheduling.models.pruning_models import Pruning
from scraping.services.parse_pruning_service import do_parse_pruning_for_website


@dataclass
class SchedulingParsingObjects:
    pruning_parsing_history_ids: list[tuple[int, int]]


def do_parse_scheduling(scheduling: Scheduling) -> SchedulingParsingObjects:
    churches = []
    for scheduling_historical_church in scheduling.historical_churches.all():
        church_history_id = scheduling_historical_church.church_history_id
        historical_church = Church.history.get(history_id=church_history_id)
        churches.append(historical_church.instance)

    all_pruning_history_ids = []
    for scraping_pruning in scheduling.scraping_prunings.all():
        all_pruning_history_ids.append(scraping_pruning.pruning_history_id)

    for image_pruning in scheduling.image_prunings.all():
        all_pruning_history_ids.append(image_pruning.pruning_history_id)

    pruning_parsing_history_ids = set()
    for pruning_history_id in all_pruning_history_ids:
        historical_pruning = Pruning.history.get(history_id=pruning_history_id)
        pruning = historical_pruning.instance

        parsing = do_parse_pruning_for_website(pruning, churches)
        if parsing is None:
            continue

        parsing_history_id = parsing.history.latest().history_id
        pruning_parsing_history_ids.add((pruning_history_id, parsing_history_id))

    return SchedulingParsingObjects(
        pruning_parsing_history_ids=list(pruning_parsing_history_ids),
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
