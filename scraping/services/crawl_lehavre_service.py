import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from fructose import Fructose

from home.models import Diocese, Parish, Church, ParishSource
from scraping.services.crawl_messesinfos_service import compute_church_coordinates

ai = Fructose(model="gpt-3.5-turbo")


@dataclass
class ChurchDataclass:
    name: str
    address: str
    zipcode: str
    city: str


@dataclass
class ParishDataclass:
    name: str
    churches: list[ChurchDataclass]


@ai
def extract_parish_and_churches(html_no_space: str) -> ParishDataclass:
    """
    Given html of a parish web page, return the name of the parish and the list of churches.
    Each church has a name and an address, a zipcode and a city.
    """
    ...


def execute_with_retry(url, max_attempts=3):
    try:
        return requests.get(url)
    except ConnectionError as e:
        print(e)
        if max_attempts <= 1:
            print('aborting...')
            return None
        print('retrying...')
        return execute_with_retry(url, max_attempts - 1)


def get_parish_urls(page):
    url = f'https://www.lehavre.catholique.fr/paroisse/page/{page}'
    r = execute_with_retry(url)
    if r.status_code != 200:
        print('lehavre website error')
        print(r.status_code)
        print(r.text)

        return None

    full_text = r.text

    # use regex to extract all urls containing 'paroisse'
    pattern = r'https://www\.lehavre\.catholique\.fr/paroisse/paroisse-[^"]+'

    # Find all matches
    urls_starting_with_paroisse = re.findall(pattern, full_text)

    return set(urls_starting_with_paroisse)


def get_churches_on_lehavre(page: int):
    messesinfo_network_id = 'lh'
    try:
        diocese = Diocese.objects.get(messesinfo_network_id=messesinfo_network_id)
    except Diocese.DoesNotExist:
        print(f'no diocese for network_id {messesinfo_network_id}')
        return None

    parish_urls = get_parish_urls(page)
    if not parish_urls:
        return None

    nb_parishes = 0
    nb_churches = 0
    for url in parish_urls:
        try:
            Parish.objects.get(home_url=url)
            print('ignoring already saved parish', url)
            continue
        except Parish.DoesNotExist:
            pass

        r = execute_with_retry(url)
        if r.status_code != 200:
            print('lehavre website error with url', url)
            print(r.status_code)
            print(r.text)

            return None

        full_html = r.text

        soup = BeautifulSoup(full_html, 'html.parser')
        main_div = soup.find('div', id='main')
        pretty_html = main_div.prettify()
        html_no_space = re.sub(r'\n\s*', '', pretty_html)

        print(url)
        parish_data = extract_parish_and_churches(html_no_space)
        print(parish_data)

        parish = Parish(
            name=parish_data.name,
            home_url=url,
        )
        parish.save()
        nb_parishes += 1

        parish_source = ParishSource(
            name=parish_data.name,
            messesinfo_network_id=None,
            messesinfo_community_id=None,
            website=parish,
            diocese=diocese
        )

        for church_data in parish_data.churches:
            church = Church(
                name=church_data.name,
                address=church_data.address,
                zipcode=church_data.zipcode,
                city=church_data.city,
                location=None,  # will be updated later
                parish_source=parish_source,
            )
            church.save()

            compute_church_coordinates(church)
            nb_churches += 1

    return nb_parishes, nb_churches
