from urllib.parse import urlparse, ParseResult, parse_qs, urlencode

from bs4 import BeautifulSoup, SoupStrainer, Comment
from bs4 import element as el

from scraping.utils.string_search import has_any_of_words
from scraping.utils.url_utils import is_internal_link, get_clean_full_url, \
    replace_scheme_and_hostname

CONFESSIONS_OR_SCHEDULES_MENTIONS = [
    'confession',
    'confessions',
    'confesser',
    'reconciliation',
    'reconcilier',
    'penitence',
    'sacrement',
    'sacrements',
    'pardon',
    'horaire',
    'horaires',
    'noel',
    'careme',
    'paques',
    'pascal',
    'priere',
    'prier',
    'etapes',
    'paroisse',
    'spirituelle',
    'info',
    'infos',
    'vivre',
]

IGNORED_EXTENSIONS = [
    # images
    '.jpg',
    '.jpeg',

    # media
    '.mp3',
    '.m4a',
    '.wav',
    '.mp4',
    '.mov',
    '.avi',
    '.mkv',
    '.webm',
    '.flv',
    '.wmv',
    '.wma',
    '.flac'

    # calendar
    '.ics',
]


def might_be_confession_link(path, text):
    last_part_of_path = path.split('/')[-1] if '/' in path else path

    if has_any_of_words(last_part_of_path, CONFESSIONS_OR_SCHEDULES_MENTIONS) \
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


def is_forbidden(url_parsed, forbidden_paths: set[str]):
    for path in forbidden_paths:
        if url_parsed.path.startswith(path):
            return True

    return False


def get_links(element: el, home_url: str, aliases_domains: set[str], forbidden_paths: set[str]
              ) -> set[str]:
    results = set()

    for link in element:
        if not link.has_attr('href'):
            continue

        full_url = link['href']
        url_parsed = urlparse(full_url)

        # If the link is like "sacrements.html", we build it from any home_url we have
        if not url_parsed.netloc:
            full_url = replace_scheme_and_hostname(url_parsed, new_url=home_url)
            url_parsed = urlparse(full_url)

        # We ignore external links (ex: facebook page...)
        if not is_internal_link(full_url, url_parsed, aliases_domains):
            continue

        # We ignore forbidden paths and their children
        if is_forbidden(url_parsed, forbidden_paths):
            continue

        full_url = get_clean_full_url(full_url)  # we use standardized url to ensure unicity
        url_parsed = urlparse(full_url)

        # If the link contains parameters we remove the non-useful ones
        if url_parsed.query:
            full_url = clean_url_query(url_parsed)
            url_parsed = urlparse(full_url)

        # If this is a link to an image or a calendar we ignore it
        if any(url_parsed.path.endswith(extension) for extension in IGNORED_EXTENSIONS):
            continue

        # Extract link text
        all_strings = link.find_all(text=lambda t: not isinstance(t, Comment),
                                    recursive=True)
        text = ' '.join(all_strings).rstrip()

        if might_be_confession_link(url_parsed.path, text):
            results.add(full_url)

    return results


def parse_content_links(content, home_url: str, aliases_domains: set[str],
                        forbidden_paths: set[str]) -> set[str]:
    try:
        element = BeautifulSoup(content, 'html.parser', parse_only=SoupStrainer('a'))
    except Exception as e:
        # TODO handle pdf properly
        print(e)
        return set()

    links = get_links(element, home_url, aliases_domains, forbidden_paths)

    return links


def remove_http_https_duplicate(extracted_html_list_by_link: dict[str, list[str]]
                                ) -> dict[str, list[str]]:
    """If links appear twice in given list with different scheme, we keep only https"""
    d = {}
    for link, extracted_html_list in extracted_html_list_by_link.items():
        link_with_https = link.replace('http://', 'https://')
        link_parsed = urlparse(link)
        d.setdefault(link_with_https, {})[link_parsed.scheme] = extracted_html_list

    results = {}
    for link_with_https, extracted_html_list_by_scheme in d.items():
        if 'https' in extracted_html_list_by_scheme:
            results[link_with_https] = extracted_html_list_by_scheme['https']
        else:
            scheme, extracted_html_list = list(extracted_html_list_by_scheme.items())[0]
            original_link = link_with_https.replace('https://', f'{scheme}://')
            results[original_link] = extracted_html_list

    return results
