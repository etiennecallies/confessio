import requests


def get_content_from_url(url):
    print(f'getting content from url {url}')

    r = requests.get(url)
    if r.status_code != 200:
        print(r.status_code)
        print(r.text)

        return None

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