from typing import Optional

import requests
from requests import RequestException

from scraping.utils.url_utils import get_domain

TIMEOUT = 10


def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    }


def get_content_length(url):
    print(f'getting content length from url {url}')

    headers = get_headers()
    try:
        r = requests.head(url, headers=headers, timeout=TIMEOUT, stream=True)
    except RequestException as e:
        print(e)
        return None

    content_length = r.headers.get('Content-Length')
    if not content_length:
        return 0

    return int(content_length)


def get_content_from_url(url):
    if url.endswith('.pdf'):
        content_length = get_content_length(url)
        if content_length is None:
            print(f'could not get content length from url {url}')
            return None

        if content_length > 10_000_000:
            print(f'content length is {content_length}, too large (>10MB)')
            return None

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


def get_url_aliases(url) -> tuple[list[tuple[str, str]], Optional[str]]:
    print(f'getting url aliases for {url}')

    headers = get_headers()
    try:
        r = requests.get(url, headers=headers, allow_redirects=False, timeout=TIMEOUT)
    except RequestException as e:
        return [], str(e)

    aliases = [(url, get_domain(url))]
    if r.status_code in [301, 302] and 'location' in r.headers:
        location = r.headers['location']
        url_aliases, error_message = get_url_aliases(location)
        if not url_aliases:
            print(f'tried to follow redirect location {location} but got error {error_message}')
        else:
            aliases.extend(url_aliases)

    return aliases, None
