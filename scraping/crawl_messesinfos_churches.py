import json

import requests
from django.contrib.gis.geos import Point

from home.models import Church, Parish


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


def get_parish(messesinfo_community_id):
    messesinfo_request = f'{{"F":"cef.kephas.shared.request.AppRequestFactory",' \
                         f'"I":[{{"O":"cAFxqYS1T1aS3fEnag2PwGf6i9w=",' \
                         f'"P":["{messesinfo_community_id}"],"R":[]}}]}}'
    parish_raw = post_messesinfo_request(messesinfo_request)
    if parish_raw is None:
        return None

    try:
        parish_data = parish_raw['O'][0]['P']

        if 'url' not in parish_data:
            print(f'no url for {messesinfo_community_id}, ignoring this parish')
            return None

        return Parish(
            name=parish_data['name'],
            home_url=parish_data['url'],
            messesinfo_network_id=parish_data['networkId'],
            messesinfo_community_id=parish_data['id'],
        )
    except (KeyError, TypeError) as e:
        print(e)
        print(json.dumps(parish_raw))
        print(messesinfo_community_id)

        return None


def get_churches_on_page(network_id, page):
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
                parish = Parish.objects.get(messesinfo_community_id=messesinfo_community_id)
            except Parish.DoesNotExist:
                parish = get_parish(messesinfo_community_id)
                if parish is None:
                    print(f'no valid parish for church {church_messesinfo_id} ignoring this church')
                    continue
                parish.save()

            church = Church(
                name=church_data['name'],
                location=Point(church_data['longitude'], church_data['latitude']),
                address=church_data['address'],
                zipcode=church_data['zipcode'],
                city=church_data['city'],
                messesinfo_id=church_messesinfo_id,
                parish=parish
            )
            church.save()
            nb_churches_saved += 1

        print(f'{nb_churches_saved} churches saved')

        return len(churches_list)

    except (KeyError, TypeError) as e:
        print(e)
        print(json.dumps(data))

        return None
