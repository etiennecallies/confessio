from typing import Set, Dict
from urllib.parse import urlparse, ParseResult, parse_qs, urlencode

from bs4 import BeautifulSoup, SoupStrainer, Comment
from bs4 import element as el

from scraping.utils.string_search import has_any_of_words
from scraping.utils.url_utils import is_internal_link, get_clean_full_url, \
    replace_scheme_and_hostname

CONFESSIONS_OR_SCHEDULES_MENTIONS = [
    'confession',
    'confessions',
    'reconciliation',
    'sacrement',
    'sacrements',
    'pardon',
    'horaire',
    'horaires',
    'noel',
    'careme',
    'paques',
    'pascal',
]


def might_be_confession_link(path, text):
    if has_any_of_words(path, CONFESSIONS_OR_SCHEDULES_MENTIONS) \
            or has_any_of_words(text, CONFESSIONS_OR_SCHEDULES_MENTIONS):
        return True

    return False


def clean_url_query(url_parsed: ParseResult):
    query = parse_qs(url_parsed.query, keep_blank_values=True)

    # We remove share parameter (share=twitter, share=facebook...)
    query.pop('share', None)

    # We remove calendar parameter (outlook-ical=1 ...)
    query.pop('ical', None)
    query.pop('outlook-ical', None)

    url_parsed = url_parsed._replace(query=urlencode(query, True))

    return url_parsed.geturl()


def get_links(element: el, home_url: str, home_url_aliases: Set[str]):
    results = set()

    for link in element:
        if link.has_attr('href'):
            full_url = link['href']
            url_parsed = urlparse(full_url)

            # If the link is like "sacrements.html", we build it from any home_url we have
            if not url_parsed.netloc:
                full_url = replace_scheme_and_hostname(url_parsed, new_url=home_url)
                url_parsed = urlparse(full_url)

            # We ignore external links (ex: facebook page...)
            if not is_internal_link(full_url, url_parsed, home_url_aliases):
                continue

            full_url = get_clean_full_url(full_url)  # we use standardized url to ensure unicity
            url_parsed = urlparse(full_url)

            # If the link contains parameters we remove the non-useful ones
            if url_parsed.query:
                full_url = clean_url_query(url_parsed)
                url_parsed = urlparse(full_url)

            # If this is a link to an image or a calendar we ignore it
            if url_parsed.path.endswith('.jpg') \
                    or url_parsed.path.endswith('.jpeg') \
                    or url_parsed.path.endswith('.ics'):
                continue

            # Extract link text
            all_strings = link.find_all(text=lambda t: not isinstance(t, Comment),
                                        recursive=True)
            text = ' '.join(all_strings).rstrip()

            if might_be_confession_link(url_parsed.path, text):
                results.add(full_url)

    return results


def parse_content_links(content, home_url: str, home_url_aliases: Set[str]):
    element = BeautifulSoup(content, 'html.parser', parse_only=SoupStrainer('a'))
    links = get_links(element, home_url, home_url_aliases)

    return links


def remove_http_https_duplicate(confession_part_by_link: Dict[str, str]) -> Dict[str, str]:
    """If links appear twice in given list with different scheme, we keep only https"""
    d = {}
    for link, confession_part in confession_part_by_link.items():
        link_with_https = link.replace('http://', 'https://')
        link_parsed = urlparse(link)
        d.setdefault(link_with_https, {})[link_parsed.scheme] = confession_part

    results = {}
    for link_with_https, confession_part_by_scheme in d.items():
        if 'https' in confession_part_by_scheme:
            results[link_with_https] = confession_part_by_scheme['https']
        else:
            scheme, confession_part = list(confession_part_by_scheme.items())[0]
            original_link = link_with_https.replace('https://', f'{scheme}://')
            results[original_link] = confession_part

    return results
