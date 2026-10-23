from dataclasses import dataclass
from uuid import UUID

from attaching.models import FileNote, TextNote
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
    text_note_by_parsing_uuid: dict[UUID, TextNote]
    all_text_notes_by_parsing_uuid: dict[UUID, list[TextNote]]
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

    # Notes
    file_note_by_parsing_uuid, all_file_notes_by_parsing_uuid = add_notes_parsings(
        scheduling_prunings_and_parsings.file_notes,
        scheduling_prunings_and_parsings.prunings_by_file_note_uuid,
        scheduling_prunings_and_parsings, prunings_by_parsing_uuid, parsings)
    text_note_by_parsing_uuid, all_text_notes_by_parsing_uuid = add_notes_parsings(
        scheduling_prunings_and_parsings.text_notes,
        scheduling_prunings_and_parsings.prunings_by_text_note_uuid,
        scheduling_prunings_and_parsings, prunings_by_parsing_uuid, parsings)

    sorted_parsings = sort_parsings(parsings)

    return WebsiteParsingsAndPrunings(
        parsings=sorted_parsings,
        scraping_by_parsing_uuid=scraping_by_parsing_uuid,
        all_scrapings_by_parsing_uuid=all_scrapings_by_parsing_uuid,
        file_note_by_parsing_uuid=file_note_by_parsing_uuid,
        all_file_notes_by_parsing_uuid=all_file_notes_by_parsing_uuid,
        text_note_by_parsing_uuid=text_note_by_parsing_uuid,
        all_text_notes_by_parsing_uuid=all_text_notes_by_parsing_uuid,
        prunings_by_parsing_uuid=prunings_by_parsing_uuid,
    )


def add_notes_parsings(notes: list[FileNote] | list[TextNote],
                       prunings_by_note_uuid: dict[UUID, list[Pruning]],
                       scheduling_prunings_and_parsings: SchedulingPrimarySources,
                       prunings_by_parsing_uuid: dict[UUID, list[Pruning]],
                       parsings: list[Parsing],
                       ) -> tuple[dict[UUID, FileNote | TextNote],
                                  dict[UUID, list[FileNote | TextNote]]]:
    note_by_parsing_uuid = {}
    all_notes_by_parsing_uuid = {}
    last_created_at_by_parsing_uuid = {}
    for note in notes:
        for pruning in prunings_by_note_uuid[note.uuid]:
            parsing = scheduling_prunings_and_parsings.parsing_by_pruning_uuid.get(pruning.uuid)
            if parsing is None:
                continue

            all_notes_by_parsing_uuid.setdefault(parsing.uuid, [])
            if note not in all_notes_by_parsing_uuid[parsing.uuid]:
                all_notes_by_parsing_uuid[parsing.uuid].append(note)
            prunings_by_parsing_uuid.setdefault(parsing.uuid, [])
            if pruning not in prunings_by_parsing_uuid[parsing.uuid]:
                prunings_by_parsing_uuid[parsing.uuid].append(pruning)
            if parsing not in parsings:
                parsings.append(parsing)

            if last_created_at_by_parsing_uuid.setdefault(parsing.uuid, None) is None \
                    or note.created_at > last_created_at_by_parsing_uuid[parsing.uuid]:
                last_created_at_by_parsing_uuid[parsing.uuid] = note.created_at
                note_by_parsing_uuid[parsing.uuid] = note

    return note_by_parsing_uuid, all_notes_by_parsing_uuid


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
    text_notes: list[TextNote]
    prunings_by_scraping_uuid: dict[UUID, Pruning]
    prunings_by_file_note_uuid: dict[UUID, Pruning]
    prunings_by_text_note_uuid: dict[UUID, Pruning]
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

    file_notes, prunings_by_file_note_uuid = get_empty_notes(
        scheduling_prunings_and_parsings.file_notes,
        scheduling_prunings_and_parsings.prunings_by_file_note_uuid,
        scheduling_prunings_and_parsings, parsings_by_pruning_uuid)
    text_notes, prunings_by_text_note_uuid = get_empty_notes(
        scheduling_prunings_and_parsings.text_notes,
        scheduling_prunings_and_parsings.prunings_by_text_note_uuid,
        scheduling_prunings_and_parsings, parsings_by_pruning_uuid)

    return WebsiteEmptySources(
        scrapings=scrapings,
        file_notes=file_notes,
        text_notes=text_notes,
        prunings_by_scraping_uuid=prunings_by_scraping_uuid,
        prunings_by_file_note_uuid=prunings_by_file_note_uuid,
        prunings_by_text_note_uuid=prunings_by_text_note_uuid,
        parsings_by_pruning_uuid=parsings_by_pruning_uuid,
    )


def get_empty_notes(notes: list[FileNote] | list[TextNote],
                    prunings_by_note_uuid: dict[UUID, list[Pruning]],
                    scheduling_prunings_and_parsings: SchedulingPrimarySources,
                    parsings_by_pruning_uuid: dict[UUID, list[Parsing]],
                    ) -> tuple[list[FileNote | TextNote], dict[UUID, list[Pruning]]]:
    empty_notes = []
    empty_prunings_by_note_uuid = {}
    for note in notes:
        prunings = prunings_by_note_uuid[note.uuid]
        if not prunings:
            empty_notes.append(note)
            continue

        is_note_to_add = handle_prunings(
            prunings,
            scheduling_prunings_and_parsings,
            empty_prunings_by_note_uuid.setdefault(note.uuid, []),
            parsings_by_pruning_uuid
        )

        if is_note_to_add:
            empty_notes.append(note)

    return empty_notes, empty_prunings_by_note_uuid


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
