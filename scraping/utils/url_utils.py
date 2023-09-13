from typing import Set
from urllib.parse import urlparse, ParseResult


def get_domain(url):
    url_parsed = urlparse(url)

    return url_parsed.netloc


def replace_scheme_and_hostname(url_parsed: ParseResult, new_url: str) -> str:
    new_url_parsed = urlparse(new_url)

    url_parsed = url_parsed._replace(scheme=new_url_parsed.scheme)
    url_parsed = url_parsed._replace(netloc=new_url_parsed.netloc)

    return url_parsed.geturl()


def get_clean_full_url(url):
    url_parsed = urlparse(url)

    url_parsed = clean_parsed_url(url_parsed)

    return url_parsed.geturl()


def clean_parsed_url(url_parsed: ParseResult) -> ParseResult:
    path = url_parsed.path
    if path.endswith('/'):
        url_parsed = url_parsed._replace(path=path[:-1])

    url_parsed = url_parsed._replace(fragment='')

    return url_parsed


def is_internal_link(url: str, url_parsed: ParseResult, home_url_aliases: Set[str]):
    if url_parsed.scheme not in ['http', 'https']:
        return False

    if url.startswith('#'):
        # link on same page
        return False

    if url_parsed.netloc not in home_url_aliases:
        # external link
        return False

    return True
