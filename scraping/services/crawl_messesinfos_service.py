import json
from typing import Optional

import requests
from django.contrib.gis.geos import Point

from home.models import Church, Parish, ParishSource, ChurchModeration, Diocese
from scraping.services.merge_parishes_service import update_parish_name
from scraping.utils.geocode_address import geocode
from scraping.utils.url_utils import get_clean_full_url


def post_messesinfo_request(messesinfo_request):
    messesinfo_url = 'https://messes.info/gwtRequest'
    messesinfo_headers = {'content-type': 'application/json; charset=UTF-8'}

    r = requests.post(messesinfo_url, headers=messesinfo_headers, data=messesinfo_request)
    if r.status_code != 200:
        print('messesinfo API error')
        print(r.status_code)
        print(r.text)

        return None

    return r.json()


def get_parish(home_url, name) -> Parish:
    try:
        parish = Parish.objects.get(home_url=home_url)

        # We update parish name (website title or concatenated names)
        update_parish_name(parish, name)
    except Parish.DoesNotExist:
        parish = Parish(
            name=name,
            home_url=home_url,
        )

        # We save parish
        parish.save()

    return parish


def fetch_parish_source(messesinfo_community_id, diocese: Diocese) -> Optional[ParishSource]:
    messesinfo_request = f'{{"F":"cef.kephas.shared.request.AppRequestFactory",' \
                         f'"I":[{{"O":"cAFxqYS1T1aS3fEnag2PwGf6i9w=",' \
                         f'"P":["{messesinfo_community_id}"],"R":[]}}]}}'
    parish_raw = post_messesinfo_request(messesinfo_request)
    if parish_raw is None:
        print(f'no data for {messesinfo_community_id}')
        return None

    try:
        parish_data = parish_raw['O'][0]['P']

        if 'url' not in parish_data:
            print(f'no url for {messesinfo_community_id}, ignoring this parish')
            return None

        url = parish_data['url']
        home_url = get_clean_full_url(url)  # we use standardized url to ensure unicity
        name = parish_data['name']

        parish = get_parish(home_url, name)

        parish_source = ParishSource(
            name=name,
            messesinfo_network_id=parish_data['networkId'],
            messesinfo_community_id=parish_data['id'],
            parish=parish,
            diocese=diocese,
        )

        return parish_source
    except (KeyError, TypeError) as e:
        print(e)
        print(json.dumps(parish_raw))
        print(messesinfo_community_id)

        return None


def get_churches_on_page(messesinfo_network_id: str, page):
    try:
        diocese = Diocese.objects.get(messesinfo_network_id=messesinfo_network_id)
    except Diocese.DoesNotExist:
        print(f'no diocese for network_id {messesinfo_network_id}')
        return None

    messesinfo_request = f'{{"F":"cef.kephas.shared.request.AppRequestFactory",' \
                         f'"I":[{{"O":"$i2wVYlJYdDXj9pOVHx42kKyAu8=",' \
                         f'"P":["DIOCESE:{messesinfo_network_id.upper()}",{page},' \
                         f'25,"48.856614:2.352222",null]}}]}}'

    print(f'fetching churches in {messesinfo_network_id} on page {page}')
    data = post_messesinfo_request(messesinfo_request)

    if data == {"S": [True], "I": [[]]}:
        print('no result')
        return 0

    try:
        churches_list = data['O']
        nb_churches_saved = 0

        for church_raw in churches_list:
            church_data = church_raw['P']

            church_messesinfo_id = church_data['id']
            if Church.objects.filter(messesinfo_id=church_messesinfo_id).exists():
                print(f'Church {church_messesinfo_id} already exists ignoring')
                continue

            messesinfo_community_id = church_data['communityId']
            try:
                parish_source = ParishSource.objects.get(
                    messesinfo_community_id=messesinfo_community_id)
            except ParishSource.DoesNotExist:
                parish_source = fetch_parish_source(messesinfo_community_id, diocese)
                if parish_source is None:
                    print(f'no valid parish for church {church_messesinfo_id} ignoring this church')
                    continue
                parish_source.save()

            church = Church(
                name=church_data['name'],
                location=Point(church_data['longitude'], church_data['latitude']),
                address=church_data['address'],
                zipcode=church_data['zipcode'],
                city=church_data['city'],
                messesinfo_id=church_messesinfo_id,
                parish=parish_source.parish,
                parish_source=parish_source,
            )
            church.save()
            nb_churches_saved += 1

            if not church.location.x or not church.location.y:
                compute_church_coordinates(church)

        print(f'{nb_churches_saved} churches saved')

        return len(churches_list)

    except (KeyError, TypeError) as e:
        print(e)
        print(json.dumps(data))

        return None


def compute_church_coordinates(church: Church):
    result = geocode(church.name, church.address, church.city, church.zipcode)
    if not result or not result.get('coordinates', None):
        category = ChurchModeration.Category.LOCATION_NULL
    else:
        longitude, latitude = result.get('coordinates')
        church.location = Point(longitude, latitude)
        if not church.address:
            church.address = result.get('address', None)
        if not church.zipcode:
            church.zipcode = result.get('zipcode', None)
        if not church.city:
            church.city = result.get('city', None)
        church.save()
        category = ChurchModeration.Category.LOCATION_FROM_API

    church_moderation = ChurchModeration(
        church=church,
        category=category,
        location=church.location
    )
    church_moderation.save()
