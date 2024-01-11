from typing import Set, Optional

import requests
from requests import RequestException

from scraping.utils.url_utils import get_domain

TIMEOUT = 3


def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    }


def get_content_from_url(url):
    print(f'getting content from url {url}')

    headers = get_headers()
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT)
    except RequestException as e:
        print(e)
        return None

    if r.status_code != 200:
        print(f'got status code {r.status_code}')

        return None

    # https://stackoverflow.com/a/52615216
    r.encoding = r.apparent_encoding

    return r.text


def get_content_from_pdf(url):
    print(f'getting content from pdf with url {url}')
    # TODO download pdf
    # TODO use poppler-utils

    return ''


def get_content(url, page_type):
    if page_type == 'html_page':
        return get_content_from_url(url)
    elif page_type == 'pdf':
        return get_content_from_pdf(url)
    else:
        print(f'unrecognized page_type {page_type}')
        return None


def get_url_aliases(url) -> Optional[Set[str]]:
    print(f'getting url aliases for {url}')

    aliases = {get_domain(url)}

    headers = get_headers()
    try:
        r = requests.get(url, headers=headers, allow_redirects=False, timeout=TIMEOUT)
    except RequestException as e:
        print(e)
        return None

    if r.status_code in [301, 302] and 'location' in r.headers:
        location = r.headers['location']
        url_aliases = get_url_aliases(location)
        if url_aliases is None:
            print(f'tried to follow redirect location {location} but got error')
        else:
            aliases.update(url_aliases)

    return aliases
