from dataclasses import dataclass
from uuid import UUID

from attaching.models import FileNote
from crawling.models import Scraping
from scheduling.models import Parsing
from scheduling.models.pruning_models import Pruning
from scheduling.public_service import scheduling_has_schedules, SchedulingPrimarySources


#########################
# PARSINGS AND PRUNINGS #
#########################

@dataclass
class WebsiteParsingsAndPrunings:
    parsings: list[Parsing]
    scraping_by_parsing_uuid: dict[UUID, Scraping]
    all_scrapings_by_parsing_uuid: dict[UUID, list[Scraping]]
    file_note_by_parsing_uuid: dict[UUID, FileNote]
    all_file_notes_by_parsing_uuid: dict[UUID, list[FileNote]]
    prunings_by_parsing_uuid: dict[UUID, list[Pruning]]


def get_website_parsings_and_prunings(
        scheduling_prunings_and_parsings: SchedulingPrimarySources
) -> WebsiteParsingsAndPrunings:
    prunings_by_parsing_uuid = {}
    parsings = []

    # Scrapings
    scraping_by_parsing_uuid = {}
    all_scrapings_by_parsing_uuid = {}
    scraping_last_created_at_by_parsing_uuid = {}
    for scraping in scheduling_prunings_and_parsings.scrapings:
        for pruning in scheduling_prunings_and_parsings.prunings_by_scraping_uuid[scraping.uuid]:
            parsing = scheduling_prunings_and_parsings.parsing_by_pruning_uuid.get(pruning.uuid)
            if parsing is None:
                continue

            all_scrapings_by_parsing_uuid.setdefault(parsing.uuid, [])
            if scraping not in all_scrapings_by_parsing_uuid[parsing.uuid]:
                all_scrapings_by_parsing_uuid[parsing.uuid].append(scraping)
            prunings_by_parsing_uuid.setdefault(parsing.uuid, [])
            if pruning not in prunings_by_parsing_uuid[parsing.uuid]:
                prunings_by_parsing_uuid[parsing.uuid].append(pruning)
            if parsing not in parsings:
                parsings.append(parsing)

            if scraping_last_created_at_by_parsing_uuid.setdefault(parsing.uuid, None) is None \
                    or scraping.created_at > scraping_last_created_at_by_parsing_uuid[parsing.uuid]:
                scraping_last_created_at_by_parsing_uuid[parsing.uuid] = scraping.created_at
                scraping_by_parsing_uuid[parsing.uuid] = scraping

    # FileNotes
    file_note_by_parsing_uuid = {}
    all_file_notes_by_parsing_uuid = {}
    last_created_at_by_parsing_uuid = {}
    for file_note in scheduling_prunings_and_parsings.file_notes:
        for pruning in scheduling_prunings_and_parsings.prunings_by_file_note_uuid[file_note.uuid]:
            parsing = scheduling_prunings_and_parsings.parsing_by_pruning_uuid.get(pruning.uuid)
            if parsing is None:
                continue

            all_file_notes_by_parsing_uuid.setdefault(parsing.uuid, [])
            if file_note not in all_file_notes_by_parsing_uuid[parsing.uuid]:
                all_file_notes_by_parsing_uuid[parsing.uuid].append(file_note)
            prunings_by_parsing_uuid.setdefault(parsing.uuid, [])
            if pruning not in prunings_by_parsing_uuid[parsing.uuid]:
                prunings_by_parsing_uuid[parsing.uuid].append(pruning)
            if parsing not in parsings:
                parsings.append(parsing)

            if last_created_at_by_parsing_uuid.setdefault(parsing.uuid, None) is None \
                    or file_note.created_at > last_created_at_by_parsing_uuid[parsing.uuid]:
                last_created_at_by_parsing_uuid[parsing.uuid] = file_note.created_at
                file_note_by_parsing_uuid[parsing.uuid] = file_note

    sorted_parsings = sort_parsings(parsings)

    return WebsiteParsingsAndPrunings(
        parsings=sorted_parsings,
        scraping_by_parsing_uuid=scraping_by_parsing_uuid,
        all_scrapings_by_parsing_uuid=all_scrapings_by_parsing_uuid,
        file_note_by_parsing_uuid=file_note_by_parsing_uuid,
        all_file_notes_by_parsing_uuid=all_file_notes_by_parsing_uuid,
        prunings_by_parsing_uuid=prunings_by_parsing_uuid,
    )


def sort_parsings(parsings: list[Parsing]) -> list[Parsing]:
    # TODO find a relevant sorting
    return list(sorted(parsings, key=lambda p: p.created_at))


#################
# EMPTY SOURCES #
#################

@dataclass
class WebsiteEmptySources:
    scrapings: list[Scraping]
    file_notes: list[FileNote]
    prunings_by_scraping_uuid: dict[UUID, Pruning]
    prunings_by_file_note_uuid: dict[UUID, Pruning]
    parsings_by_pruning_uuid: dict[UUID, list[Parsing]]


def get_empty_sources(scheduling_prunings_and_parsings: SchedulingPrimarySources
                      ) -> WebsiteEmptySources:
    parsings_by_pruning_uuid = {}

    scrapings = []
    prunings_by_scraping_uuid = {}
    for scraping in scheduling_prunings_and_parsings.scrapings:
        prunings = scheduling_prunings_and_parsings.prunings_by_scraping_uuid[scraping.uuid]
        if not prunings:
            scrapings.append(scraping)
            continue

        is_scraping_to_add = handle_prunings(
            prunings,
            scheduling_prunings_and_parsings,
            prunings_by_scraping_uuid.setdefault(scraping.uuid, []),
            parsings_by_pruning_uuid
        )

        if is_scraping_to_add:
            scrapings.append(scraping)

    file_notes = []
    prunings_by_file_note_uuid = {}
    for file_note in scheduling_prunings_and_parsings.file_notes:
        prunings = scheduling_prunings_and_parsings.prunings_by_file_note_uuid[file_note.uuid]
        if not prunings:
            file_notes.append(file_note)
            continue

        is_file_note_to_add = handle_prunings(
            prunings,
            scheduling_prunings_and_parsings,
            prunings_by_file_note_uuid.setdefault(file_note.uuid, []),
            parsings_by_pruning_uuid
        )

        if is_file_note_to_add:
            file_notes.append(file_note)

    return WebsiteEmptySources(
        scrapings=scrapings,
        file_notes=file_notes,
        prunings_by_scraping_uuid=prunings_by_scraping_uuid,
        prunings_by_file_note_uuid=prunings_by_file_note_uuid,
        parsings_by_pruning_uuid=parsings_by_pruning_uuid,
    )


def add_pruning_if_empty(parsing: Parsing | None, pruning: Pruning, prunings: list[Pruning],
                         parsings_by_pruning_uuid: dict[UUID, list[Parsing]]) -> bool:
    if parsing is None or not scheduling_has_schedules(parsing):
        prunings.append(pruning)
        if parsing:
            parsings_by_pruning_uuid.setdefault(pruning.uuid, []).append(parsing)
        return True

    return False


def handle_prunings(prunings: list[Pruning],
                    scheduling_prunings_and_parsings: SchedulingPrimarySources,
                    prunings_of_object: list[Pruning],
                    parsings_by_pruning_uuid: dict[UUID, list[Parsing]]) -> bool:
    is_object_to_add = False
    for pruning in prunings:
        parsing = scheduling_prunings_and_parsings.parsing_by_pruning_uuid.get(pruning.uuid)
        is_object_to_add = add_pruning_if_empty(
            parsing, pruning, prunings_of_object, parsings_by_pruning_uuid) or is_object_to_add

    return is_object_to_add
