from typing import Optional, Tuple, Dict

from scraping.utils.download_content import get_content_from_url, get_url_aliases
from scraping.utils.extract_content import extract_confession_part_from_content
from scraping.utils.extract_links import parse_content_links, remove_http_https_duplicate

MAX_VISITED_LINKS = 50


def search_for_confession_pages(home_url) -> Tuple[Dict[str, str], int, Optional[str]]:
    home_url_aliases = get_url_aliases(home_url)
    if home_url_aliases is None:
        return {}, 0, 'error in get_url_aliases'

    visited_links = set()
    links_to_visit = {home_url}
    confession_parts_seen = set()

    error_detail = None

    results = {}
    while len(links_to_visit) > 0 and len(visited_links) < MAX_VISITED_LINKS:
        link = links_to_visit.pop()
        visited_links.add(link)

        html_content = get_content_from_url(link)
        if html_content is None:
            # something went wrong (e.g. 404), we just ignore this page
            continue

        # Looking if new confession part is found
        confession_part = extract_confession_part_from_content(html_content)
        if confession_part and confession_part not in confession_parts_seen:
            results[link] = confession_part
            confession_parts_seen.add(confession_part)

        # Looking for new links to visit
        new_links = parse_content_links(html_content, home_url, home_url_aliases)
        for new_link in new_links:
            if new_link not in visited_links:
                links_to_visit.add(new_link)

    if len(visited_links) == MAX_VISITED_LINKS:
        error_detail = f'Reached limit of {MAX_VISITED_LINKS} visited links.'

    return remove_http_https_duplicate(results), len(visited_links), error_detail


if __name__ == '__main__':
    # home_url = 'https://www.eglise-saintgermaindespres.fr/'
    # home_url = 'https://www.saintjacquesduhautpas.com/'
    # home_url = 'https://paroisses-amplepuis-thizy.blogspot.fr/'
    # home_url = 'https://paroissesaintbruno.pagesperso-orange.fr/'
    home_url = 'https://paroissecroixrousse.fr/'
    print(search_for_confession_pages(home_url))
