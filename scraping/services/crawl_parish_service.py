from typing import Tuple, Optional

from django.db.models.functions import Now

from home.models import Parish, Crawling, Page, ParishModeration
from scraping.services.scrape_page_service import upsert_scraping
from scraping.utils.download_and_search_urls import search_for_confession_pages


def remove_not_validated_moderation(parish: Parish, category: ParishModeration.Category):
    try:
        moderation = ParishModeration.objects.get(parish=parish, category=category)
        if moderation.validated_at is None:
            moderation.delete()
    except ParishModeration.DoesNotExist:
        pass


def add_moderation(parish: Parish, category: ParishModeration.Category):
    try:
        ParishModeration.objects.get(parish=parish, category=category)
    except ParishModeration.DoesNotExist:
        moderation = ParishModeration(
            parish=parish, category=category,
            name=parish.name, home_url=parish.home_url
        )
        moderation.save()


def crawl_parish(parish: Parish) -> Tuple[bool, bool, Optional[str]]:
    # Actually crawling parish
    confession_parts_by_url, nb_visited_links, error_detail = \
        search_for_confession_pages(parish.home_url)

    # Inserting global statistics
    crawling = Crawling(
        nb_visited_links=nb_visited_links,
        nb_success_links=len(confession_parts_by_url),
        error_detail=error_detail,
        parish=parish,
    )
    crawling.save()

    # Removing old pages
    existing_pages = parish.get_pages()
    existing_urls = list(map(lambda p: p.url, existing_pages))
    for page in existing_pages:
        if page.url not in confession_parts_by_url:
            # Page did exist but not anymore
            page.deleted_at = Now()
            page.save()
        else:
            # Page still exists, we update scraping
            confession_part = confession_parts_by_url[page.url]
            upsert_scraping(page, confession_part)

    if confession_parts_by_url:
        # Adding new pages
        for url in confession_parts_by_url:
            if url not in existing_urls:
                # New page was found

                new_page = Page(
                    url=url,
                    parish=parish
                )
                new_page.save()

                # Insert or update scraping
                confession_part = confession_parts_by_url[url]
                upsert_scraping(new_page, confession_part)

        remove_not_validated_moderation(parish, ParishModeration.Category.HOME_URL_NO_RESPONSE)
        remove_not_validated_moderation(parish, ParishModeration.Category.HOME_URL_NO_CONFESSION)

        return True, True, None
    elif nb_visited_links > 0:
        remove_not_validated_moderation(parish, ParishModeration.Category.HOME_URL_NO_RESPONSE)
        add_moderation(parish, ParishModeration.Category.HOME_URL_NO_CONFESSION)

        return False, True, None
    else:
        add_moderation(parish, ParishModeration.Category.HOME_URL_NO_RESPONSE)
        remove_not_validated_moderation(parish, ParishModeration.Category.HOME_URL_NO_CONFESSION)

        return False, False, error_detail

