import json
from typing import Optional

import requests
from django.contrib.gis.geos import Point

from home.models import Church, Parish, ParishSource, ParishModeration, ChurchModeration, Diocese
from scraping.utils.extract_title import get_page_title
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


def add_moderation(parish: Parish, category: ParishModeration.Category, home_url):
    try:
        # we need to delete existing moderation first
        existing_category = ParishModeration.objects.get(parish=parish, category=category)
        existing_category.delete()
    except ParishModeration.DoesNotExist:
        pass

    parish_moderation = ParishModeration(
        parish=parish,
        category=category,
        name=parish.name,
        home_url=home_url,
    )
    parish_moderation.save()


def get_parish(home_url, name, diocese: Diocese) -> Parish:
    try:
        parish = Parish.objects.get(home_url=home_url)
        page_title = get_page_title(home_url)

        if page_title:
            # If home_url's title exists we replace parish name by it
            parish.name = page_title
            moderation_category = ParishModeration.Category.NAME_WEBSITE_TITLE
        else:
            # If there is a problem with home_url, new name is concatenation of all names
            previous_sources = parish.sources.all()
            all_names = list(map(lambda s: s.name, previous_sources)) + [name]
            concatenated_name = ' - '.join(all_names)
            print(f'got new name {concatenated_name}')

            parish.name = concatenated_name
            moderation_category = ParishModeration.Category.NAME_CONCATENATED

        # We update parish
        parish.save()

        # We will need to moderate generated parish name
        add_moderation(parish, moderation_category, home_url)

    except Parish.DoesNotExist:
        parish = Parish(
            name=name,
            home_url=home_url,
            diocese=diocese,
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

        parish = get_parish(home_url, name, diocese)

        parish_source = ParishSource(
            name=name,
            messesinfo_network_id=parish_data['networkId'],
            messesinfo_community_id=parish_data['id'],
            parish=parish)

        return parish_source
    except (KeyError, TypeError) as e:
        print(e)
        print(json.dumps(parish_raw))
        print(messesinfo_community_id)

        return None


def get_churches_on_page(network_id, page):
    try:
        diocese = Diocese.objects.get(messesinfo_network_id=network_id)
    except Diocese.DoesNotExist:
        print(f'no diocese for network_id {network_id}')
        return None

    messesinfo_request = f'{{"F":"cef.kephas.shared.request.AppRequestFactory",' \
                         f'"I":[{{"O":"$i2wVYlJYdDXj9pOVHx42kKyAu8=",' \
                         f'"P":["{network_id}",{page},25,"48.856614:2.352222",null]}}]}}'

    print(f'fetching churches in {network_id} on page {page}')
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
                coordinates = geocode(church.name, church.address, church.city, church.zipcode)
                if not coordinates:
                    category = ChurchModeration.Category.LOCATION_NULL
                else:
                    longitude, latitude = coordinates
                    church.location = Point(longitude, latitude)
                    church.save()
                    category = ChurchModeration.Category.LOCATION_FROM_API

                church_moderation = ChurchModeration(
                    church=church,
                    category=category,
                    location=church.location
                )
                church_moderation.save()

        print(f'{nb_churches_saved} churches saved')

        return len(churches_list)

    except (KeyError, TypeError) as e:
        print(e)
        print(json.dumps(data))

        return None
