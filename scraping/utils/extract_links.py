from typing import Set, List
from urllib.parse import urlparse, ParseResult

from bs4 import BeautifulSoup, SoupStrainer, Comment
from bs4 import element as el

from scraping.utils.string_search import has_any_of_words

CONFESSIONS_OR_SCHEDULES_MENTIONS = [
    'confession',
    'confessions',
    'reconciliation',
    'sacrement',
    'sacrements',
    'horaire',
    'horaires',
]


def might_be_confession_link(path, text):
    if has_any_of_words(path, CONFESSIONS_OR_SCHEDULES_MENTIONS) \
            or has_any_of_words(text, CONFESSIONS_OR_SCHEDULES_MENTIONS):
        return True

    return False


def is_internal_link(url: str, url_parsed: ParseResult, home_url_aliases: Set[str]):
    if url.startswith('#'):
        # link on same page
        return False

    if url_parsed.netloc not in home_url_aliases:
        # external link
        return False

    return True


def get_links(element: el, home_url_aliases: Set[str]):
    results = set()

    for link in element:
        if link.has_attr('href'):
            full_url = link['href']
            url_parsed = urlparse(full_url)

            if not is_internal_link(full_url, url_parsed, home_url_aliases):
                continue

            # Extract link text
            all_strings = link.find_all(text=lambda t: not isinstance(t, Comment),
                                        recursive=True)
            text = ' '.join(all_strings).rstrip()

            if might_be_confession_link(url_parsed.path, text):
                results.add(full_url)

    return results


def parse_content_links(content, home_url_aliases: Set[str]):
    element = BeautifulSoup(content, 'html.parser', parse_only=SoupStrainer('a'))
    links = get_links(element, home_url_aliases)

    return links


def remove_http_https_duplicate(links: list) -> List[str]:
    """If links appear twice in given list with different scheme, we keep only https"""
    d = {}
    for link in links:
        link_with_https = link.replace('http://', 'https://')
        link_parsed = urlparse(link)
        d.setdefault(link_with_https, set()).add(link_parsed.scheme)

    results = []
    for link_with_https, schemes in d.items():
        if 'https' in schemes:
            results.append(link_with_https)
        else:
            results.append(link_with_https.replace('https://', f'{list(schemes)[0]}://'))

    return results
