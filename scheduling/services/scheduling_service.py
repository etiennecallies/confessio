from home.models import Parsing
from scheduling.models import Scheduling


def get_scheduling_parsings(scheduling: Scheduling) -> list[Parsing]:
    all_parsings = []
    for pruning_parsing in scheduling.pruning_parsings.all():
        parsing_history_id = pruning_parsing.parsing_history_id
        historical_parsing = Parsing.history.get(history_id=parsing_history_id)
        parsing = historical_parsing.instance
        all_parsings.append(parsing)

    return all_parsings
