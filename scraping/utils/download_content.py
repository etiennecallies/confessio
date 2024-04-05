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


def get_url_aliases(url) -> tuple[list[str], Optional[str]]:
    print(f'getting url aliases for {url}')

    headers = get_headers()
    try:
        r = requests.get(url, headers=headers, allow_redirects=False, timeout=TIMEOUT)
    except RequestException as e:
        return [], str(e)

    aliases = [get_domain(url)]
    if r.status_code in [301, 302] and 'location' in r.headers:
        location = r.headers['location']
        url_aliases, error_message = get_url_aliases(location)
        if url_aliases is None:
            print(f'tried to follow redirect location {location} but got error {error_message}')
        else:
            aliases.extend(url_aliases)

    return aliases, None
