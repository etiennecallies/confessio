import asyncio

from bs4 import BeautifulSoup

from scraping.download.download_content import get_content_from_url


async def get_page_title(url):
    html = await get_content_from_url(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('title')
    if not title:
        return None

    title_name = title.string.strip()
    print(f'got title {title_name}')

    return title_name


if __name__ == '__main__':
    print(asyncio.run(get_page_title('http://www.montsdelamadeleine.fr/')))
