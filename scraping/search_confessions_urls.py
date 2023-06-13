from typing import Optional, List, Tuple

from scraping.utils.download_content import get_content_from_url, get_url_aliases
from scraping.utils.extract_content import extract_confession_part_from_content
from scraping.utils.extract_links import parse_content_links, remove_http_https_duplicate

MAX_VISITED_LINKS = 100


def search_for_confession_pages(home_url) -> Tuple[List[str], int, Optional[str]]:
    home_url_aliases = get_url_aliases(home_url)
    if home_url_aliases is None:
        return [], 0, 'error in get_url_aliases'

    visited_links = set()
    links_to_visit = {home_url}

    error_detail = None

    results = []
    while len(links_to_visit) > 0 and len(visited_links) < MAX_VISITED_LINKS:
        link = links_to_visit.pop()
        visited_links.add(link)

        content = get_content_from_url(link)
        if content is None:
            # something went wrong (e.g. 404), we just ignore this page
            continue

        confession_part = extract_confession_part_from_content(content, 'html_page')
        if confession_part:
            results.append(link)

        new_links = parse_content_links(content, home_url, home_url_aliases)
        for new_link in new_links:
            if new_link not in visited_links:
                links_to_visit.add(new_link)

    return remove_http_https_duplicate(results), len(visited_links), error_detail


if __name__ == '__main__':
    # home_url = 'https://www.eglise-saintgermaindespres.fr/'
    # home_url = 'https://www.saintjacquesduhautpas.com/'
    # home_url = 'https://paroisses-amplepuis-thizy.blogspot.fr/'
    # home_url = 'https://paroissesaintbruno.pagesperso-orange.fr/'
    home_url = 'https://paroissecroixrousse.fr/'
    print(search_for_confession_pages(home_url))
