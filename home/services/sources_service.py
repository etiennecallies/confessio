from dataclasses import dataclass
from uuid import UUID

from home.models import Website, Parsing, Page, Pruning, Image
from scraping.services.image_service import get_image_html
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


def get_website_parsings_and_prunings(website: Website) -> WebsiteParsingsAndPrunings:
    sources = get_website_sorted_parsings(website)
    prunings_by_parsing_uuid = {}

    # Pages
    page_by_parsing_uuid = {}
    all_pages_by_parsing_uuid = {}
    page_scraping_last_created_at_by_parsing_uuid = {}
    for page in website.get_pages():
        if page.scraping is None:
            continue

        for pruning in page.get_prunings():
            parsing = page.get_parsing(pruning)
            if parsing is None or not has_schedules(parsing):
                continue

            page_scraping_last_created_at = page_scraping_last_created_at_by_parsing_uuid.get(
                parsing.uuid, None)
            if page_scraping_last_created_at is None \
                    or page.scraping.created_at > page_scraping_last_created_at:
                page_scraping_last_created_at_by_parsing_uuid[parsing.uuid] = \
                    page.scraping.created_at
                page_by_parsing_uuid[parsing.uuid] = page

            all_pages_by_parsing_uuid.setdefault(parsing.uuid, []).append(page)
            prunings_by_parsing_uuid.setdefault(parsing.uuid, []).append(pruning)

    # Images
    image_by_parsing_uuid = {}
    all_images_by_parsing_uuid = {}
    image_last_created_at_by_parsing_uuid = {}
    for image in website.images.all():
        if get_image_html(image) is None:
            continue

        for pruning in image.prunings.all():
            parsing = pruning.get_parsing(website)
            if parsing is None or not has_schedules(parsing):
                continue

            image_last_created_at = image_last_created_at_by_parsing_uuid.get(parsing.uuid, None)
            if image_last_created_at is None or image.created_at > image_last_created_at:
                image_last_created_at_by_parsing_uuid[parsing.uuid] = image.created_at
                image_by_parsing_uuid[parsing.uuid] = image

            all_images_by_parsing_uuid.setdefault(parsing.uuid, []).append(image)
            prunings_of_parsing = prunings_by_parsing_uuid.setdefault(parsing.uuid, [])
            if pruning not in prunings_of_parsing:
                prunings_of_parsing.append(pruning)

    return WebsiteParsingsAndPrunings(
        sources=sources,
        page_by_parsing_uuid=page_by_parsing_uuid,
        all_pages_by_parsing_uuid=all_pages_by_parsing_uuid,
        image_by_parsing_uuid=image_by_parsing_uuid,
        all_images_by_parsing_uuid=all_images_by_parsing_uuid,
        prunings_by_parsing_uuid=prunings_by_parsing_uuid,
    )


def get_website_sorted_parsings(website: Website) -> list[Parsing]:
    # TODO find a relevant sorting
    return list(sorted([p for p in website.parsings.all() if has_schedules(p)],
                       key=lambda p: p.created_at))


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
