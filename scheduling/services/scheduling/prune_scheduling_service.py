from dataclasses import dataclass

from attaching.models import FileNote
from crawling.models import Scraping
from scheduling.models import Scheduling, ScrapingPruning, FileNotePruning
from scheduling.services.pruning.prune_scraping_service import prune_pruning


@dataclass
class SchedulingPruningObjects:
    scraping_pruning_history_ids: list[tuple[int, int]]
    file_note_pruning_history_ids: list[tuple[int, int]]


def do_prune_scheduling(scheduling: Scheduling) -> SchedulingPruningObjects:
    scraping_pruning_history_ids = []
    for scheduling_historical_scraping in scheduling.historical_scrapings.all():
        scraping_history_id = scheduling_historical_scraping.scraping_history_id
        historical_scraping = Scraping.history.get(history_id=scraping_history_id)
        scraping = historical_scraping.instance

        for pruning in scraping.prunings.all():
            prune_pruning(pruning)

            pruning_history_id = pruning.history.latest().history_id
            scraping_pruning_history_ids.append((scraping_history_id, pruning_history_id))

    file_note_pruning_history_ids = []
    for scheduling_historical_file_note in scheduling.historical_file_notes.all():
        file_note_history_id = scheduling_historical_file_note.file_note_history_id
        historical_file_note = FileNote.history.get(history_id=file_note_history_id)
        file_note = historical_file_note.instance

        for pruning in file_note.prunings.all():
            prune_pruning(pruning)

            pruning_history_id = pruning.history.latest().history_id
            file_note_pruning_history_ids.append((file_note_history_id, pruning_history_id))

    return SchedulingPruningObjects(
        scraping_pruning_history_ids=scraping_pruning_history_ids,
        file_note_pruning_history_ids=file_note_pruning_history_ids,
    )


def bulk_create_scheduling_pruning_objects(
        scheduling: Scheduling,
        scheduling_pruning_objects: SchedulingPruningObjects):
    # ScrapingPruning
    scraping_objs = [
        ScrapingPruning(
            scheduling=scheduling,
            scraping_history_id=scraping_history_id,
            pruning_history_id=pruning_history_id,
        ) for scraping_history_id, pruning_history_id
        in scheduling_pruning_objects.scraping_pruning_history_ids
    ]
    ScrapingPruning.objects.bulk_create(scraping_objs)

    # FileNotePruning
    file_note_objs = [
        FileNotePruning(
            scheduling=scheduling,
            file_note_history_id=file_note_history_id,
            pruning_history_id=pruning_history_id,
        ) for file_note_history_id, pruning_history_id
        in scheduling_pruning_objects.file_note_pruning_history_ids
    ]
    FileNotePruning.objects.bulk_create(file_note_objs)
