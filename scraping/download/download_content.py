from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from requests import RequestException

from scraping.utils.url_utils import get_domain, are_similar_urls, replace_scheme_and_hostname

TIMEOUT = 20
MAX_SIZE = 5_000_000


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
        return get_content_length_by_streaming(url)

    return int(content_length)


def get_content_length_by_streaming(url: str) -> int | None:
    print(f'getting content length by streaming from url {url}')

    headers = get_headers()
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT, stream=True)
    except RequestException as e:
        print(e)
        return None

    r.raw.decode_content = False

    total_size = 0
    for chunk in r.iter_content(chunk_size=8192):
        total_size += len(chunk)
        if total_size > MAX_SIZE:
            print("File size exceeds limit. Download aborted.")
            return None

    return total_size


def get_content_from_url(url):
    # Handle heavy pdf files
    if url.endswith('.pdf'):
        content_length = get_content_length(url)
        if content_length is None:
            print(f'could not get content length from url {url}')
            return None

        if content_length > MAX_SIZE:
            print(f'content length is {content_length}, too large (>5MB)')
            return None
        else:
            print(f'content length is {content_length}')

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


def get_meta_refresh_redirect(soup: BeautifulSoup) -> Optional[str]:
    meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
    if meta_refresh:
        content = meta_refresh.get('content', '')
        # The content usually looks like "0; url=http://example.com"
        parts = content.split(';')
        if len(parts) > 1 and 'url=' in parts[1]:
            return parts[1].split('url=')[1].strip()

    return None


def get_url_aliases(url) -> tuple[list[tuple[str, str]], Optional[str]]:
    print(f'getting url aliases for {url}')

    headers = get_headers()
    try:
        r = requests.get(url, headers=headers, allow_redirects=False, timeout=TIMEOUT)
    except RequestException as e:
        return [], str(e)

    aliases = [(url, get_domain(url))]
    redirect_url = None

    if r.status_code in [301, 302] and 'location' in r.headers:
        redirect_url = r.headers['location']
    elif r.status_code == 200:
        try:
            soup = BeautifulSoup(r.text, 'html.parser')
        except Exception as e:
            print(e)
            # TODO handle pdf correctly
            return aliases, str(e)
        redirect_url = get_meta_refresh_redirect(soup)

    if redirect_url:
        redirect_url_parsed = urlparse(redirect_url)

        # If the link is like "sacrements.html", we build it from the url we have
        if not redirect_url_parsed.netloc:
            redirect_url = replace_scheme_and_hostname(redirect_url_parsed, new_url=url)

        url_aliases, error_message = get_url_aliases(redirect_url)
        if not url_aliases:
            print(f'tried to follow redirect location {redirect_url} but got error {error_message}')
        else:
            aliases.extend(url_aliases)

    return aliases, None


def redirects_to_other_url(url1: str, url2: str) -> bool:
    if are_similar_urls(url1, url2):
        return True

    aliases, _ = get_url_aliases(url1)
    for url, domain in aliases:
        if are_similar_urls(url, url2):
            return True
    return False


def get_url_redirection(url: str):
    aliases, _ = get_url_aliases(url)
    if not aliases:
        return None

    return aliases[-1][0]
