from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from home.models import Website, Parsing, Page, Pruning
from scraping.services.parsing_service import has_schedules


#########################
# PARSINGS AND PRUNINGS #
#########################

@dataclass
class WebsiteParsingsAndPrunings:
    sources: list[Parsing]
    page_by_parsing_uuid: dict[UUID, Page]
    all_pages_by_parsing_uuid: dict[UUID, list[Page]]
    prunings_by_parsing_uuid: dict[UUID, list[Pruning]]
    page_scraping_last_created_at_by_parsing_uuid: dict[UUID, Optional[datetime]]


def get_website_parsings_and_prunings(website: Website) -> WebsiteParsingsAndPrunings:
    sources = get_website_sorted_parsings(website)
    page_by_parsing_uuid = {}
    all_pages_by_parsing_uuid = {}
    prunings_by_parsing_uuid = {}
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

    return WebsiteParsingsAndPrunings(
        sources=sources,
        page_by_parsing_uuid=page_by_parsing_uuid,
        all_pages_by_parsing_uuid=all_pages_by_parsing_uuid,
        prunings_by_parsing_uuid=prunings_by_parsing_uuid,
        page_scraping_last_created_at_by_parsing_uuid=page_scraping_last_created_at_by_parsing_uuid,
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
    prunings_by_page_uuid: dict[UUID, Pruning]
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
            if parsing is None or not has_schedules(parsing):
                is_page_to_add = True
                prunings_by_page_uuid.setdefault(page.uuid, []).append(pruning)
                if parsing:
                    parsings_by_pruning_uuid.setdefault(pruning.uuid, []).append(parsing)

        if is_page_to_add:
            pages.append(page)

    return WebsiteEmptySources(
        pages=pages,
        prunings_by_page_uuid=prunings_by_page_uuid,
        parsings_by_pruning_uuid=parsings_by_pruning_uuid,
    )
