from scraping.utils.download_content import get_content_from_url
from scraping.utils.extract_content import extract_confession_part_from_content
from scraping.utils.extract_links import parse_content_links

MAX_VISITED_LINKS = 100


def search_for_confession_pages(home_url):
    visited_links = set()
    links_to_visit = {home_url}

    results = []
    while len(links_to_visit) > 0 and len(visited_links) < MAX_VISITED_LINKS:
        link = links_to_visit.pop()
        visited_links.add(link)

        content = get_content_from_url(link)
        confession_part = extract_confession_part_from_content(content, 'html_page')
        if confession_part:
            results.append(link)

        new_links = parse_content_links(content, home_url)
        for new_link in new_links:
            if new_link not in visited_links:
                links_to_visit.add(new_link)

    return results


if __name__ == '__main__':
    home_url = 'https://www.eglise-saintgermaindespres.fr/'
    # home_url = 'https://www.saintjacquesduhautpas.com/'
    print(search_for_confession_pages(home_url))
