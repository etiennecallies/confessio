from typing import Tuple, Optional

from home.models import Website, Crawling, Page, WebsiteModeration
from scraping.crawl.download_and_search_urls import search_for_confession_pages
from scraping.download.download_content import get_url_aliases
from scraping.services.page_service import delete_page
from scraping.services.scrape_page_service import upsert_extracted_html_list
from scraping.utils.url_utils import get_clean_full_url, get_path, get_domain


def remove_not_validated_moderation(website: Website, category: WebsiteModeration.Category):
    try:
        moderation = WebsiteModeration.objects.get(website=website, category=category,
                                                   validated_at__isnull=True)
        moderation.delete()
    except WebsiteModeration.DoesNotExist:
        pass


def add_moderation(website: Website, category: WebsiteModeration.Category,
                   other_website: Optional[Website] = None,
                   other_home_url: Optional[str] = None):
    if website.unreliability_reason is not None:
        # we do not add moderation for unreliable website
        return

    try:
        WebsiteModeration.objects.get(website=website, category=category)
    except WebsiteModeration.DoesNotExist:
        moderation = WebsiteModeration(
            website=website, category=category,
            other_website=other_website,
            home_url=other_home_url or website.home_url
        )
        moderation.save()


def update_home_url(website: Website, new_home_url: str):
    if len(new_home_url) > 200:
        add_moderation(website, WebsiteModeration.Category.HOME_URL_TOO_LONG,
                       other_home_url=new_home_url)
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


def do_crawl_website(website: Website) -> tuple[dict[str, list[str]], int, Optional[str]]:
    # Get home_url aliases
    home_url_aliases, error_message = get_url_aliases(website.home_url)
    if not home_url_aliases:
        return {}, 0, f'error in get_url_aliases: {error_message}'

    new_home_url = get_clean_full_url(home_url_aliases[-1][0])

    # Update home_url if needed
    if website.home_url != new_home_url:
        update_home_url(website, new_home_url)

    aliases_domains = set([alias[1] for alias in home_url_aliases])

    # Get any other website starting with the same home_url
    forbidden_paths = set()
    for alias_domain in aliases_domains:
        same_domain_websites = Website.objects\
            .filter(home_url__contains=alias_domain, is_active=True)\
            .exclude(uuid=website.uuid).all()
        for other_website in same_domain_websites:
            if get_domain(other_website.home_url) in aliases_domains:
                forbidden_paths.add(get_path(other_website.home_url))

    # Actually crawling website
    return search_for_confession_pages(new_home_url, aliases_domains, forbidden_paths)


def crawl_website(website: Website) -> Tuple[bool, bool, Optional[str]]:
    # check if website has parish
    if not website.parishes.exists():
        website.delete()
        return False, False, 'website has no parish'

    extracted_html_list_by_url, nb_visited_links, error_detail = do_crawl_website(website)

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

        remove_not_validated_moderation(website, WebsiteModeration.Category.HOME_URL_NO_RESPONSE)

        if website.one_page_has_confessions():
            remove_not_validated_moderation(website,
                                            WebsiteModeration.Category.HOME_URL_NO_CONFESSION)
            return True, True, None

        add_moderation(website, WebsiteModeration.Category.HOME_URL_NO_CONFESSION)
        return False, True, None

    elif nb_visited_links > 0:
        remove_not_validated_moderation(website, WebsiteModeration.Category.HOME_URL_NO_RESPONSE)
        add_moderation(website, WebsiteModeration.Category.HOME_URL_NO_CONFESSION)

        return False, True, None
    else:
        add_moderation(website, WebsiteModeration.Category.HOME_URL_NO_RESPONSE)
        remove_not_validated_moderation(website, WebsiteModeration.Category.HOME_URL_NO_CONFESSION)

        return False, False, error_detail
