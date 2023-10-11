from typing import Tuple, Optional

from django.db.models.functions import Now

from home.models import Parish, Crawling, Page
from scraping.services.scrape_page_service import upsert_scraping
from scraping.utils.download_and_search_urls import search_for_confession_pages


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

        return True, True, None
    elif nb_visited_links > 0:
        return False, True, None
    else:
        return False, False, error_detail

