from datetime import date
from typing import Optional

from home.models import Website, Crawling, Page, WebsiteModeration, Church, Pruning
from home.utils.async_utils import run_in_sync
from home.utils.log_utils import info
from scraping.crawl.download_and_search_urls import search_for_confession_pages, \
    get_new_url_and_aliases, forbid_diocese_home_links
from scraping.services.page_service import delete_page
from scraping.services.prune_scraping_service import prune_pruning, update_parsings
from scraping.services.schedules_conflict_service import website_has_schedules_conflict
from scraping.services.scrape_page_service import upsert_extracted_html_list
from scraping.utils.url_utils import get_path, get_domain, have_similar_domain


def remove_not_validated_moderation(website: Website, category: WebsiteModeration.Category):
    try:
        moderation = WebsiteModeration.objects.get(website=website, category=category,
                                                   validated_at__isnull=True)
        moderation.delete()
    except WebsiteModeration.DoesNotExist:
        pass


def add_moderation(website: Website, category: WebsiteModeration.Category,
                   other_website: Optional[Website] = None,
                   other_home_url: Optional[str] = None,
                   conflict_day: date | None = None,
                   conflict_church: Church | None = None):
    if website.unreliability_reason is not None:
        # we do not add moderation for unreliable website
        return

    try:
        moderation = WebsiteModeration.objects.get(website=website, category=category)
        moderation.conflict_day = conflict_day
        moderation.conflict_church = conflict_church
        moderation.save()
    except WebsiteModeration.DoesNotExist:
        moderation = WebsiteModeration(
            website=website, category=category,
            other_website=other_website,
            home_url=other_home_url[:200] if other_home_url else website.home_url,
            diocese=website.get_diocese(),
            conflict_day=conflict_day,
            conflict_church=conflict_church,
        )
        moderation.save()


def update_home_url(website: Website, new_home_url: str):
    if len(new_home_url) > 200:
        add_moderation(website, WebsiteModeration.Category.HOME_URL_TOO_LONG,
                       other_home_url=new_home_url)
        return

    not_eligible_urls = [
        'google.com/sorry',
        'accounts.google.com',
    ]
    for not_eligible_url in not_eligible_urls:
        if not_eligible_url in new_home_url:
            print(f'This url is not eligible to home url update: {new_home_url}')
            return

    # Check that there is not already a Website with this home_url
    try:
        website_with_url = Website.objects.get(home_url=new_home_url)
        print(f'conflict between website {website.name} ({website.uuid}) '
              f'and {website_with_url.name} ({website_with_url.uuid}) '
              f'about url {new_home_url} Adding moderation.')
        add_moderation(website, WebsiteModeration.Category.HOME_URL_CONFLICT, website_with_url)
    except Website.DoesNotExist:
        print(f'replacing home_url from {website.home_url} to {new_home_url} '
              f'for website {website.name}')
        website.home_url = new_home_url
        website.save()
        remove_not_validated_moderation(website, WebsiteModeration.Category.HOME_URL_CONFLICT)


async def handle_diocese_domain(website: Website, domain_has_changed: bool,
                                aliases_domains: set[str],
                                forbidden_paths: set[str], path_redirection: dict[str, str]):
    diocese = await website.async_get_diocese()
    if diocese and diocese.home_url:
        if domain_has_changed:
            print('check if diocese home_url has changed')
            new_diocese_url, diocese_aliases_domains, error_message = \
                await get_new_url_and_aliases(diocese.home_url)
            if error_message:
                print(f'error in get_new_url_and_aliases for diocese with url {diocese.home_url}: '
                      f'{error_message}')
            elif new_diocese_url != diocese.home_url:
                print('it has changed! Replacing it.')
                diocese.home_url = new_diocese_url
                await diocese.asave()

        if have_similar_domain(website.home_url, diocese.home_url):
            print('Website and diocese have similar domain, forbidding diocese home links')
            forbidden_paths |= await forbid_diocese_home_links(diocese.home_url,
                                                               aliases_domains,
                                                               path_redirection)


async def do_crawl_website(website: Website) -> tuple[dict[str, list[str]], int, Optional[str]]:
    # Get home_url aliases
    new_home_url, aliases_domains, error_message = await get_new_url_and_aliases(website.home_url)
    if error_message:
        return {}, 0, f'error in get_url_aliases: {error_message}'

    # Update home_url if needed
    if website.home_url != new_home_url:
        domain_has_changed = True
        await run_in_sync(update_home_url, website, new_home_url)
    else:
        domain_has_changed = False

    # Get any other website starting with the same home_url
    forbidden_paths = set()
    for alias_domain in aliases_domains:
        same_domain_websites = Website.objects\
            .filter(home_url__contains=alias_domain, is_active=True)\
            .exclude(uuid=website.uuid).all()
        async for other_website in same_domain_websites:
            if get_domain(other_website.home_url) in aliases_domains:
                forbidden_paths.add(get_path(other_website.home_url))

    path_redirection = {}
    await handle_diocese_domain(website,
                                domain_has_changed, aliases_domains, forbidden_paths,
                                path_redirection)

    # Actually crawling website
    return await search_for_confession_pages(new_home_url, aliases_domains, forbidden_paths,
                                             path_redirection)


async def crawl_website(website: Website) -> tuple[bool, bool]:
    # check if website has parish
    if not await website.parishes.aexists():
        await website.adelete()
        info('website has no parish')
        return False, False

    extracted_html_list_by_url, nb_visited_links, error_detail = await do_crawl_website(website)

    prunings_to_prune = await run_in_sync(process_extracted_html_and_insert_crawling,
                                          website,
                                          extracted_html_list_by_url,
                                          nb_visited_links,
                                          error_detail)

    for pruning in prunings_to_prune:
        await update_parsings(pruning)

    return await run_in_sync(add_moderations,
                             website,
                             bool(extracted_html_list_by_url),
                             nb_visited_links > 0)


def process_extracted_html_and_insert_crawling(
        website: Website,
        extracted_html_list_by_url: dict[str, list[str]],
        nb_visited_links: int,
        error_detail: Optional[str]
) -> list[Pruning]:
    # Inserting global statistics
    crawling = Crawling(
        nb_visited_links=nb_visited_links,
        nb_success_links=len(extracted_html_list_by_url),
        error_detail=error_detail,
    )
    crawling.save()

    last_crawling = website.crawling
    website.crawling = crawling
    website.save()
    if last_crawling:
        last_crawling.delete()

    # Removing old pages
    existing_pages = website.get_pages()
    existing_urls = list(map(lambda p: p.url, existing_pages))
    prunings_to_prune = []
    for page in existing_pages:
        if page.url not in extracted_html_list_by_url:
            # Page did exist but not anymore, we remove it
            delete_page(page)
        else:
            # Page still exists, we update scraping
            prunings_to_prune += upsert_extracted_html_list(page,
                                                            extracted_html_list_by_url[page.url])

    if extracted_html_list_by_url:
        # Adding new pages
        for url in extracted_html_list_by_url:
            if url not in existing_urls:
                # New page was found

                new_page = Page(
                    url=url,
                    website=website
                )
                new_page.save()

                # Insert or update scraping
                prunings_to_prune += upsert_extracted_html_list(new_page,
                                                                extracted_html_list_by_url[url])

    for pruning in prunings_to_prune:
        prune_pruning(pruning, no_parsing=True)

    return prunings_to_prune


def add_moderations(website: Website,
                    has_results: bool,
                    has_visited_links: bool,
                    ) -> tuple[bool, bool]:
    if has_results:
        remove_not_validated_moderation(website, WebsiteModeration.Category.HOME_URL_NO_RESPONSE)

        if website.one_page_has_confessions():
            remove_not_validated_moderation(website,
                                            WebsiteModeration.Category.HOME_URL_NO_CONFESSION)
            conflict = website_has_schedules_conflict(website)
            if conflict is None:
                remove_not_validated_moderation(website,
                                                WebsiteModeration.Category.SCHEDULES_CONFLICT)
            else:
                conflict_day, conflict_church = conflict
                add_moderation(website, WebsiteModeration.Category.SCHEDULES_CONFLICT,
                               conflict_day=conflict_day, conflict_church=conflict_church)

            return True, True

        add_moderation(website, WebsiteModeration.Category.HOME_URL_NO_CONFESSION)
        remove_not_validated_moderation(website, WebsiteModeration.Category.SCHEDULES_CONFLICT)
        return False, True

    elif has_visited_links:
        remove_not_validated_moderation(website, WebsiteModeration.Category.HOME_URL_NO_RESPONSE)
        add_moderation(website, WebsiteModeration.Category.HOME_URL_NO_CONFESSION)
        remove_not_validated_moderation(website, WebsiteModeration.Category.SCHEDULES_CONFLICT)

        return False, True
    else:
        add_moderation(website, WebsiteModeration.Category.HOME_URL_NO_RESPONSE)
        remove_not_validated_moderation(website, WebsiteModeration.Category.HOME_URL_NO_CONFESSION)
        remove_not_validated_moderation(website, WebsiteModeration.Category.SCHEDULES_CONFLICT)

        return False, False
