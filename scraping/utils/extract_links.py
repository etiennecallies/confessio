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


def is_internal_link(url: str, url_parsed: ParseResult, home_url_parsed: ParseResult):
    if url.startswith('#'):
        # link on same page
        return False

    if url_parsed.netloc != home_url_parsed.netloc:
        # external link
        return False

    return True


def get_links(element: el, home_url: str):
    home_url_parsed = urlparse(home_url)

    results = set()

    for link in element:
        if link.has_attr('href'):
            full_url = link['href']
            url_parsed = urlparse(full_url)

            if not is_internal_link(full_url, url_parsed, home_url_parsed):
                continue

            # Extract link text
            all_strings = link.find_all(text=lambda t: not isinstance(t, Comment),
                                        recursive=True)
            text = ' '.join(all_strings).rstrip()

            if might_be_confession_link(url_parsed.path, text):
                results.add(full_url)

    return results


def parse_content_links(content, home_url):
    element = BeautifulSoup(content, 'html.parser', parse_only=SoupStrainer('a'))
    links = get_links(element, home_url)

    return links
