from home.models import Parsing
from scheduling.models import Scheduling, IndexEvent
from scraping.services.index_events_service import build_website_church_events


def do_index_scheduling(scheduling: Scheduling) -> list[IndexEvent]:
    all_parsings = []
    for pruning_parsing in scheduling.pruning_parsings.all():
        parsing_history_id = pruning_parsing.parsing_history_id
        historical_parsing = Parsing.history.get(history_id=parsing_history_id)
        parsing = historical_parsing.instance
        all_parsings.append(parsing)

    church_index_events = build_website_church_events(scheduling.website, parsings=all_parsings)
    index_events = []
    for church_index_event in church_index_events:
        index_events.append(
            IndexEvent(
                scheduling=scheduling,
                church=church_index_event.church,
                day=church_index_event.day,
                start_time=church_index_event.start_time,
                indexed_end_time=church_index_event.indexed_end_time,
                displayed_end_time=church_index_event.displayed_end_time,
                is_explicitely_other=church_index_event.is_explicitely_other,
                has_been_moderated=church_index_event.has_been_moderated,
                church_color=church_index_event.church_color,
            )
        )

    return index_events
