from typing import Optional

from home.models import Website, Crawling, Page, WebsiteModeration
from home.utils.async_utils import run_in_sync
from home.utils.log_utils import info
from scraping.crawl.download_and_search_urls import search_for_confession_pages, \
    get_new_url_and_aliases, forbid_diocese_home_links
from scraping.services.page_service import delete_page
from scraping.services.scrape_page_service import upsert_extracted_html_list
from scraping.services.website_moderation_service import remove_not_validated_moderation, \
    add_moderation
from scraping.utils.url_utils import get_path, get_domain, have_similar_domain


def update_home_url(website: Website, new_home_url: str):
    if len(new_home_url) > 200:
        add_moderation(website, WebsiteModeration.Category.HOME_URL_TOO_LONG,
                       other_home_url=new_home_url)
        return

    not_eligible_urls = [
        'google.com/sorry',
        'accounts.google.com',
        'wp-admin/install.php',
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
            info('check if diocese home_url has changed')
            new_diocese_url, diocese_aliases_domains, error_message = \
                await get_new_url_and_aliases(diocese.home_url)
            if error_message:
                info(f'error in get_new_url_and_aliases for diocese with url {diocese.home_url}: '
                     f'{error_message}')
            elif new_diocese_url != diocese.home_url:
                info(f'it has changed! Replacing it. New url: {new_diocese_url}')
                diocese.home_url = new_diocese_url
                await diocese.asave()

        if have_similar_domain(website.home_url, diocese.home_url):
            info('Website and diocese have similar domain, forbidding diocese home links')
            forbidden_paths |= await forbid_diocese_home_links(diocese.home_url,
                                                               aliases_domains,
                                                               path_redirection)


async def do_crawl_website(website: Website) -> tuple[dict[str, list[str]], int, Optional[str]]:
    if not website.enabled_for_crawling:
        return {}, 0, None

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
    forbidden_outer_paths = set()
    for alias_domain in aliases_domains:
        same_domain_websites = Website.objects\
            .filter(home_url__contains=alias_domain, is_active=True)\
            .exclude(uuid=website.uuid).all()
        async for other_website in same_domain_websites:
            if get_domain(other_website.home_url) in aliases_domains:
                forbidden_outer_paths.add(get_path(other_website.home_url))

    path_redirection = {}
    await handle_diocese_domain(website,
                                domain_has_changed, aliases_domains, forbidden_outer_paths,
                                path_redirection)

    forbidden_paths = set()
    async for forbidden_path in website.forbidden_paths.all():
        print(f'Adding forbidden path {forbidden_path.path} for website {website.name}')
        forbidden_paths.add(forbidden_path.path)

    # Actually crawling website
    return await search_for_confession_pages(new_home_url, aliases_domains, forbidden_outer_paths,
                                             path_redirection, forbidden_paths)


async def crawl_website(website: Website) -> tuple[bool, bool]:
    # check if website has parish
    if not await website.parishes.aexists():
        await website.adelete()
        info('website has no parish')
        return False, False

    extracted_html_list_by_url, nb_visited_links, error_detail = await do_crawl_website(website)

    await run_in_sync(process_extracted_html,
                      website,
                      extracted_html_list_by_url)

    return await run_in_sync(save_crawling_and_add_moderation,
                             website,
                             len(extracted_html_list_by_url),
                             nb_visited_links,
                             error_detail,
                             )


def process_extracted_html(
        website: Website,
        extracted_html_list_by_url: dict[str, list[str]],
):
    # Removing old pages
    existing_pages = website.get_pages()
    existing_urls = list(map(lambda p: p.url, existing_pages))
    for page in existing_pages:
        if page.url not in extracted_html_list_by_url:
            # Page did exist but not anymore, we remove it
            delete_page(page)
        else:
            # Page still exists, we update scraping
            upsert_extracted_html_list(page, extracted_html_list_by_url[page.url])

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
                upsert_extracted_html_list(new_page, extracted_html_list_by_url[url])


def save_crawling_and_add_moderation(website: Website,
                                     nb_success_links: int,
                                     nb_visited_links: int,
                                     error_detail: str | None = None,
                                     ) -> tuple[bool, bool]:
    if not website.enabled_for_crawling:
        return False, False

    # Inserting global statistics
    crawling = Crawling(
        nb_visited_links=nb_visited_links,
        nb_success_links=nb_success_links,
        error_detail=error_detail,
    )
    crawling.save()

    last_crawling = website.crawling
    website.crawling = crawling
    website.save()
    if last_crawling:
        last_crawling.delete()

    # Add moderation
    if nb_success_links > 0:
        remove_not_validated_moderation(website, WebsiteModeration.Category.HOME_URL_NO_RESPONSE)

        if website.one_page_has_confessions():
            remove_not_validated_moderation(website,
                                            WebsiteModeration.Category.HOME_URL_NO_CONFESSION)

            return True, True

        add_moderation(website, WebsiteModeration.Category.HOME_URL_NO_CONFESSION)
        return False, True

    elif nb_visited_links > 0:
        remove_not_validated_moderation(website, WebsiteModeration.Category.HOME_URL_NO_RESPONSE)
        add_moderation(website, WebsiteModeration.Category.HOME_URL_NO_CONFESSION)

        return False, True
    else:
        add_moderation(website, WebsiteModeration.Category.HOME_URL_NO_RESPONSE)
        remove_not_validated_moderation(website, WebsiteModeration.Category.HOME_URL_NO_CONFESSION)

        return False, False


##################
# SPLIT WEBSITES #
##################

def split_websites_for_crawling(websites: list[Website], n: int) -> list[list[Website]]:
    chunks = [[] for _ in range(n)]
    length_by_chunk_index = {i: 0 for i in range(n)}
    chunk_index_by_hostname = {}

    for website in websites:
        website_hostname = get_domain(website.home_url)
        if website_hostname in chunk_index_by_hostname:
            chunk_index = chunk_index_by_hostname[website_hostname]
        else:
            min_size = min(length_by_chunk_index.values())
            chunk_index = min(chunk_index for chunk_index, size in length_by_chunk_index.items()
                              if size == min_size)
            chunk_index_by_hostname[website_hostname] = chunk_index

        chunks[chunk_index].append(website)
        length_by_chunk_index[chunk_index] += 1

    return chunks
