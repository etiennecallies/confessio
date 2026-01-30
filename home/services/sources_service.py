from dataclasses import dataclass
from uuid import UUID

from attaching.models import Image
from crawling.models import Scraping
from scheduling.models.parsing_models import Parsing
from scheduling.models.pruning_models import Pruning
from scheduling.services.scheduling_service import SchedulingPrimarySources
from scraping.services.parsing_service import has_schedules


#########################
# PARSINGS AND PRUNINGS #
#########################

@dataclass
class WebsiteParsingsAndPrunings:
    parsings: list[Parsing]
    scraping_by_parsing_uuid: dict[UUID, Scraping]
    all_scrapings_by_parsing_uuid: dict[UUID, list[Scraping]]
    image_by_parsing_uuid: dict[UUID, Image]
    all_images_by_parsing_uuid: dict[UUID, list[Image]]
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

    # Images
    image_by_parsing_uuid = {}
    all_images_by_parsing_uuid = {}
    image_last_created_at_by_parsing_uuid = {}
    for image in scheduling_prunings_and_parsings.images:
        for pruning in scheduling_prunings_and_parsings.prunings_by_image_uuid[image.uuid]:
            parsing = scheduling_prunings_and_parsings.parsing_by_pruning_uuid.get(pruning.uuid)
            if parsing is None:
                continue

            all_images_by_parsing_uuid.setdefault(parsing.uuid, [])
            if image not in all_images_by_parsing_uuid[parsing.uuid]:
                all_images_by_parsing_uuid[parsing.uuid].append(image)
            prunings_by_parsing_uuid.setdefault(parsing.uuid, [])
            if pruning not in prunings_by_parsing_uuid[parsing.uuid]:
                prunings_by_parsing_uuid[parsing.uuid].append(pruning)
            if parsing not in parsings:
                parsings.append(parsing)

            if image_last_created_at_by_parsing_uuid.setdefault(parsing.uuid, None) is None \
                    or image.created_at > image_last_created_at_by_parsing_uuid[parsing.uuid]:
                image_last_created_at_by_parsing_uuid[parsing.uuid] = image.created_at
                image_by_parsing_uuid[parsing.uuid] = image

    sorted_parsings = sort_parsings(parsings)

    return WebsiteParsingsAndPrunings(
        parsings=sorted_parsings,
        scraping_by_parsing_uuid=scraping_by_parsing_uuid,
        all_scrapings_by_parsing_uuid=all_scrapings_by_parsing_uuid,
        image_by_parsing_uuid=image_by_parsing_uuid,
        all_images_by_parsing_uuid=all_images_by_parsing_uuid,
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
    images: list[Image]
    prunings_by_scraping_uuid: dict[UUID, Pruning]
    prunings_by_image_uuid: dict[UUID, Pruning]
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

    images = []
    prunings_by_image_uuid = {}
    for image in scheduling_prunings_and_parsings.images:
        prunings = scheduling_prunings_and_parsings.prunings_by_image_uuid[image.uuid]
        if not prunings:
            images.append(image)
            continue

        is_image_to_add = handle_prunings(
            prunings,
            scheduling_prunings_and_parsings,
            prunings_by_image_uuid.setdefault(image.uuid, []),
            parsings_by_pruning_uuid
        )

        if is_image_to_add:
            images.append(image)

    return WebsiteEmptySources(
        scrapings=scrapings,
        images=images,
        prunings_by_scraping_uuid=prunings_by_scraping_uuid,
        prunings_by_image_uuid=prunings_by_image_uuid,
        parsings_by_pruning_uuid=parsings_by_pruning_uuid,
    )


def add_pruning_if_empty(parsing: Parsing | None, pruning: Pruning, prunings: list[Pruning],
                         parsings_by_pruning_uuid: dict[UUID, list[Parsing]]) -> bool:
    if parsing is None or not has_schedules(parsing):
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
