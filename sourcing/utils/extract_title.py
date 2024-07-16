from bs4 import BeautifulSoup

from scraping.utils.download_content import get_content_from_url


def get_page_title(url):
    html = get_content_from_url(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('title')
    if not title:
        return None

    title_name = title.string
    print(f'got title {title_name}')

    return title_name


if __name__ == '__main__':
    print(get_page_title('http://www.montsdelamadeleine.fr/'))

