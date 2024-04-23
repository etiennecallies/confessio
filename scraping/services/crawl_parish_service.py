from typing import Tuple, Optional

from django.db.models.functions import Now

from home.models import Parish, Crawling, Page, ParishModeration, ScrapingModeration
from scraping.services.scrape_page_service import upsert_scraping
from scraping.utils.download_and_search_urls import search_for_confession_pages
from scraping.utils.download_content import get_url_aliases
from scraping.utils.url_utils import get_clean_full_url, get_path, get_domain


def remove_not_validated_moderation(parish: Parish, category: ParishModeration.Category):
    try:
        moderation = ParishModeration.objects.get(parish=parish, category=category,
                                                  validated_at__isnull=True)
        moderation.delete()
    except ParishModeration.DoesNotExist:
        pass


def remove_not_validated_moderation_for_page(page: Page):
    moderations = ScrapingModeration.objects.filter(scraping__page__exact=page,
                                                    validated_at__isnull=True)
    for moderation in moderations:
        moderation.delete()


def add_moderation(parish: Parish, category: ParishModeration.Category,
                   other_parish: Optional[Parish] = None):
    try:
        ParishModeration.objects.get(parish=parish, category=category)
    except ParishModeration.DoesNotExist:
        moderation = ParishModeration(
            parish=parish, category=category,
            name=parish.name, home_url=parish.home_url,
            other_parish=other_parish,
        )
        moderation.save()


def do_crawl_parish(parish: Parish) -> tuple[dict[str, str], int, Optional[str]]:
    # Get home_url aliases
    home_url_aliases, error_message = get_url_aliases(parish.home_url)
    if not home_url_aliases:
        return {}, 0, f'error in get_url_aliases: {error_message}'

    new_home_url = get_clean_full_url(home_url_aliases[-1][0])

    # Update home_url if needed
    if parish.home_url != new_home_url:
        # Check that there is not already a Parish with this home_url
        try:
            parish_with_url = Parish.objects.get(home_url=new_home_url)
            print(f'conflict between parish {parish.name} ({parish.uuid}) '
                  f'and {parish_with_url.name} ({parish_with_url.uuid}) '
                  f'about url {new_home_url} Adding moderation.')
            add_moderation(parish, ParishModeration.Category.HOME_URL_CONFLICT, parish_with_url)
        except Parish.DoesNotExist:
            print(f'replacing home_url from {parish.home_url} to {new_home_url} '
                  f'for parish {parish.name}')
            parish.home_url = new_home_url
            parish.save()
            remove_not_validated_moderation(parish, ParishModeration.Category.HOME_URL_CONFLICT)

    aliases_domains = set([alias[1] for alias in home_url_aliases])

    # Get any other parish starting with the same home_url
    forbidden_paths = set()
    for alias_domain in aliases_domains:
        same_domain_parishes = Parish.objects.filter(home_url__contains=alias_domain).exclude(
            uuid=parish.uuid).all()
        for other_parish in same_domain_parishes:
            if get_domain(other_parish.home_url) in aliases_domains:
                forbidden_paths.add(get_path(other_parish.home_url))

    # Actually crawling parish
    return search_for_confession_pages(new_home_url, aliases_domains, forbidden_paths)


def crawl_parish(website: Parish) -> Tuple[bool, bool, Optional[str]]:
    confession_parts_by_url, nb_visited_links, error_detail = do_crawl_parish(website)

    # Inserting global statistics
    crawling = Crawling(
        nb_visited_links=nb_visited_links,
        nb_success_links=len(confession_parts_by_url),
        error_detail=error_detail,
        website=website,
    )
    crawling.save()

    # Removing old pages
    existing_pages = website.get_pages()
    existing_urls = list(map(lambda p: p.url, existing_pages))
    for page in existing_pages:
        if page.url not in confession_parts_by_url:
            # We remove all pending scraping moderations related to this page
            remove_not_validated_moderation_for_page(page)

            # Page did exist but not anymore, we remove it
            page.delete()
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
                    website=website
                )
                new_page.save()

                # Insert or update scraping
                confession_part = confession_parts_by_url[url]
                upsert_scraping(new_page, confession_part)

        remove_not_validated_moderation(website, ParishModeration.Category.HOME_URL_NO_RESPONSE)
        remove_not_validated_moderation(website, ParishModeration.Category.HOME_URL_NO_CONFESSION)

        return True, True, None
    elif nb_visited_links > 0:
        remove_not_validated_moderation(website, ParishModeration.Category.HOME_URL_NO_RESPONSE)
        add_moderation(website, ParishModeration.Category.HOME_URL_NO_CONFESSION)

        return False, True, None
    else:
        add_moderation(website, ParishModeration.Category.HOME_URL_NO_RESPONSE)
        remove_not_validated_moderation(website, ParishModeration.Category.HOME_URL_NO_CONFESSION)

        return False, False, error_detail

