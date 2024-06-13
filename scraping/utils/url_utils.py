from urllib.parse import urlparse, ParseResult


def get_domain(url):
    url_parsed = urlparse(url)

    return url_parsed.netloc


def get_path(url):
    url_parsed = urlparse(url)

    return url_parsed.path


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

    netloc = url_parsed.netloc
    if netloc.endswith(' '):
        url_parsed = url_parsed._replace(netloc=netloc.strip())

    return url_parsed


def is_internal_link(url: str, url_parsed: ParseResult, aliases_domains: set[str]):
    if url_parsed.scheme not in ['http', 'https']:
        return False

    if url.startswith('#'):
        # link on same page
        return False

    if url_parsed.netloc not in aliases_domains:
        # external link
        return False

    return True


def are_similar_domain(url1: str, url2: str):
    url1_parsed = urlparse(url1)
    url2_parsed = urlparse(url2)

    domain1 = url1_parsed.netloc.replace('www.', '').split('.')[:-1]
    domain2 = url2_parsed.netloc.replace('www.', '').split('.')[:-1]

    return domain1 == domain2


def are_similar_path(url1: str, url2: str):
    url1_parsed = urlparse(url1)
    url2_parsed = urlparse(url2)

    path1 = url1_parsed.path
    if path1.endswith('/'):
        path1 = path1[:-1]

    path2 = url2_parsed.path
    if path2.endswith('/'):
        path2 = path2[:-1]

    return path1 == path2


def are_similar_urls(url1: str, url2: str):
    # if urls are the same, they are similar
    if url1 == url2:
        return True

    if are_similar_domain(url1, url2) and are_similar_path(url1, url2):
        return True

    return False
