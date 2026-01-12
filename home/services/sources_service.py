from dataclasses import dataclass
from uuid import UUID

from home.models import Website, Parsing, Page, Pruning, Image
from scheduling.models import Scheduling
from scheduling.services.scheduling_service import get_scheduling_parsings, \
    get_scheduling_prunings_and_parsings, SchedulingPruningsAndParsings
from scraping.services.parsing_service import has_schedules


#########################
# PARSINGS AND PRUNINGS #
#########################

@dataclass
class WebsiteParsingsAndPrunings:
    sources: list[Parsing]
    page_by_parsing_uuid: dict[UUID, Page]
    all_pages_by_parsing_uuid: dict[UUID, list[Page]]
    image_by_parsing_uuid: dict[UUID, Image]
    all_images_by_parsing_uuid: dict[UUID, list[Image]]
    prunings_by_parsing_uuid: dict[UUID, list[Pruning]]


def get_website_scheduling_prunings_and_parsings(website: Website
                                                 ) -> SchedulingPruningsAndParsings:
    scheduling = website.schedulings.filter(status=Scheduling.Status.INDEXED).first()
    if scheduling is None:
        return SchedulingPruningsAndParsings()

    return get_scheduling_prunings_and_parsings(scheduling)


def get_website_parsings_and_prunings(
        scheduling_prunings_and_parsings: SchedulingPruningsAndParsings
) -> WebsiteParsingsAndPrunings:
    prunings_by_parsing_uuid = {}
    parsings = []

    # Pages
    page_by_parsing_uuid = {}
    all_pages_by_parsing_uuid = {}
    scraping_last_created_at_by_parsing_uuid = {}
    for scraping in scheduling_prunings_and_parsings.scrapings:
        page = scraping.page
        for pruning in scheduling_prunings_and_parsings.prunings_by_scraping_uuid[scraping.uuid]:
            parsing = scheduling_prunings_and_parsings.parsing_by_pruning_uuid.get(pruning.uuid)
            if parsing is None:
                continue

            all_pages_by_parsing_uuid.setdefault(parsing.uuid, [])
            if page not in all_pages_by_parsing_uuid[parsing.uuid]:
                all_pages_by_parsing_uuid[parsing.uuid].append(page)
            prunings_by_parsing_uuid.setdefault(parsing.uuid, [])
            if pruning not in prunings_by_parsing_uuid[parsing.uuid]:
                prunings_by_parsing_uuid[parsing.uuid].append(pruning)
            if parsing not in parsings:
                parsings.append(parsing)

            if scraping_last_created_at_by_parsing_uuid.setdefault(parsing.uuid, None) is None \
                    or scraping.created_at > scraping_last_created_at_by_parsing_uuid[parsing.uuid]:
                scraping_last_created_at_by_parsing_uuid[parsing.uuid] = scraping.created_at
                page_by_parsing_uuid[parsing.uuid] = page

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

    sources = sort_parsings(parsings)

    return WebsiteParsingsAndPrunings(
        sources=sources,
        page_by_parsing_uuid=page_by_parsing_uuid,
        all_pages_by_parsing_uuid=all_pages_by_parsing_uuid,
        image_by_parsing_uuid=image_by_parsing_uuid,
        all_images_by_parsing_uuid=all_images_by_parsing_uuid,
        prunings_by_parsing_uuid=prunings_by_parsing_uuid,
    )


def get_website_sorted_parsings(scheduling: Scheduling) -> list[Parsing]:
    parsings = get_scheduling_parsings(scheduling)

    return sort_parsings(parsings)


def sort_parsings(parsings: list[Parsing]) -> list[Parsing]:
    # TODO find a relevant sorting
    return list(sorted(parsings, key=lambda p: p.created_at))


#################
# EMPTY SOURCES #
#################

@dataclass
class WebsiteEmptySources:
    pages: list[Page]
    images: list[Image]
    prunings_by_page_uuid: dict[UUID, Pruning]
    prunings_by_image_uuid: dict[UUID, Pruning]
    parsings_by_pruning_uuid: dict[UUID, list[Parsing]]


def get_empty_sources(scheduling_prunings_and_parsings: SchedulingPruningsAndParsings
                      ) -> WebsiteEmptySources:
    parsings_by_pruning_uuid = {}

    pages = []
    prunings_by_page_uuid = {}
    for scraping in scheduling_prunings_and_parsings.scrapings:
        page = scraping.page

        prunings = scheduling_prunings_and_parsings.prunings_by_scraping_uuid[scraping.uuid]
        if not prunings:
            pages.append(page)
            continue

        is_page_to_add = handle_prunings(
            prunings,
            scheduling_prunings_and_parsings,
            prunings_by_page_uuid.setdefault(page.uuid, []),
            parsings_by_pruning_uuid
        )

        if is_page_to_add:
            pages.append(page)

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
        pages=pages,
        images=images,
        prunings_by_page_uuid=prunings_by_page_uuid,
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
                    scheduling_prunings_and_parsings: SchedulingPruningsAndParsings,
                    prunings_of_object: list[Pruning],
                    parsings_by_pruning_uuid: dict[UUID, list[Parsing]]) -> bool:
    is_object_to_add = False
    for pruning in prunings:
        parsing = scheduling_prunings_and_parsings.parsing_by_pruning_uuid.get(pruning.uuid)
        is_object_to_add = add_pruning_if_empty(
            parsing, pruning, prunings_of_object, parsings_by_pruning_uuid) or is_object_to_add

    return is_object_to_add
