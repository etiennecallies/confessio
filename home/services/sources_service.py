from dataclasses import dataclass, field
from uuid import UUID

from home.models import Website, Parsing, Page, Pruning, Image
from scheduling.models import Scheduling
from scheduling.services.scheduling_service import get_scheduling_parsings, \
    get_scheduling_parsings_and_prunings
from scraping.services.image_service import get_image_html
from scraping.services.parsing_service import has_schedules


#########################
# PARSINGS AND PRUNINGS #
#########################

@dataclass
class WebsiteParsingsAndPrunings:
    sources: list[Parsing] = field(default_factory=list)
    page_by_parsing_uuid: dict[UUID, Page] = field(default_factory=dict)
    all_pages_by_parsing_uuid: dict[UUID, list[Page]] = field(default_factory=dict)
    image_by_parsing_uuid: dict[UUID, Image] = field(default_factory=dict)
    all_images_by_parsing_uuid: dict[UUID, list[Image]] = field(default_factory=dict)
    prunings_by_parsing_uuid: dict[UUID, list[Pruning]] = field(default_factory=dict)


def get_website_parsings_and_prunings(website: Website) -> WebsiteParsingsAndPrunings:
    scheduling = website.schedulings.filter(status=Scheduling.Status.INDEXED).first()
    if scheduling is None:
        return WebsiteParsingsAndPrunings()

    scheduling_parsings_and_prunings = get_scheduling_parsings_and_prunings(scheduling)

    sources = sort_parsings(scheduling_parsings_and_prunings.parsings)
    prunings_by_parsing_uuid = scheduling_parsings_and_prunings.prunings_by_parsing_uuid

    # Pages
    page_by_parsing_uuid = {}
    all_pages_by_parsing_uuid = {}
    for parsing_uuid, scrapings \
            in scheduling_parsings_and_prunings.scrapings_by_parsing_uuid.items():
        scraping_last_created_at = None
        all_pages_by_parsing_uuid[parsing_uuid] = []
        for scraping in scrapings:
            page = scraping.page
            if page.scraping is None:
                continue

            if scraping_last_created_at is None or scraping.created_at > scraping_last_created_at:
                scraping_last_created_at = scraping.created_at
                page_by_parsing_uuid[parsing_uuid] = page

            all_pages_by_parsing_uuid[parsing_uuid].append(page)

    # Images
    image_by_parsing_uuid = {}
    all_images_by_parsing_uuid = {}
    for parsing_uuid, images \
            in scheduling_parsings_and_prunings.images_by_parsing_uuid.items():
        image_last_created_at = None
        all_images_by_parsing_uuid[parsing_uuid] = []
        for image in images:
            if get_image_html(image) is None:
                continue

            if image_last_created_at is None or image.created_at > image_last_created_at:
                image_last_created_at = image.created_at
                image_by_parsing_uuid[parsing_uuid] = image

            all_images_by_parsing_uuid[parsing_uuid].append(image)

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


def get_empty_sources(website: Website) -> WebsiteEmptySources:
    pages = []
    prunings_by_page_uuid = {}
    parsings_by_pruning_uuid = {}
    for page in website.get_pages():
        if page.scraping is None:
            continue

        prunings = page.get_prunings()
        if not prunings:
            pages.append(page)
            continue

        is_page_to_add = False
        for pruning in page.get_prunings():
            parsing = page.get_parsing(pruning)
            is_page_to_add = add_pruning_if_empty(
                parsing, pruning, prunings_by_page_uuid.setdefault(page.uuid, []),
                parsings_by_pruning_uuid) or is_page_to_add

        if is_page_to_add:
            pages.append(page)

    images = []
    prunings_by_image_uuid = {}
    for image in website.images.all():
        if get_image_html(image) is None:
            continue

        prunings_all = image.prunings.all()
        if len(prunings_all) == 0:
            images.append(image)
            continue

        is_image_to_add = False
        for pruning in prunings_all:
            parsing = pruning.get_parsing(website)
            is_image_to_add = add_pruning_if_empty(
                parsing, pruning, prunings_by_image_uuid.setdefault(image.uuid, []),
                parsings_by_pruning_uuid) or is_image_to_add

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
