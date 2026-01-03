from scheduling.models import Scheduling, IndexEvent
from scraping.services.index_events_service import build_website_church_events


def do_index_scheduling(scheduling: Scheduling) -> list[IndexEvent]:
    return build_website_church_events(scheduling.website, scheduling)
