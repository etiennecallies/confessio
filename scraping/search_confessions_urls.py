from scraping.utils.download_content import get_content_from_url
from scraping.utils.extract_links import parse_content_links


def fetch_list_of_links(home_url: str):
    content = get_content_from_url(home_url)

    return parse_content_links(content, home_url)


if __name__ == '__main__':
    home_url = 'https://www.eglise-saintgermaindespres.fr/'
    # home_url = 'https://www.saintjacquesduhautpas.com/'
    fetch_list_of_links(home_url)
