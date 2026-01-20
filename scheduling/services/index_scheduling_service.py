from scheduling.models import Scheduling, IndexEvent
from scheduling.models.parsing_models import Parsing
from scraping.services.index_events_service import build_website_church_events
from scraping.services.parse_pruning_service import remove_useless_moderation_for_parsing


def do_index_scheduling(scheduling: Scheduling) -> list[IndexEvent]:
    return build_website_church_events(scheduling.website, scheduling)


def clean_parsings_moderations(parsing_history_ids: list[int]):
    for parsing_history_id in parsing_history_ids:
        historical_parsing = Parsing.history.get(history_id=parsing_history_id)
        parsing = historical_parsing.instance
        remove_useless_moderation_for_parsing(parsing)
