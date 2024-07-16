from dataclasses import dataclass
from typing import Optional

import requests
from django.contrib.postgres.lookups import Unaccent
from django.db.models import Value
from django.db.models.functions import Replace, Lower

from home.models import Parish, Church
from home.utils.department_utils import get_departments_context
from scraping.utils.string_search import unhyphen_content, normalize_content
from sourcing.utils.string_utils import get_string_similarity

MAX_AUTOCOMPLETE_RESULTS = 15


@dataclass
class AutocompleteResult:
    type: str
    name: str
    context: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    website_uuid: Optional[str] = None

    @classmethod
    def from_parish(cls, parish: Parish) -> 'AutocompleteResult':
        # TODO save context in parish, and create a command to fill it

        cities = set()
        zipcodes = set()
        for church in parish.churches.all():
            if church.city:
                cities.add(church.city)
            if church.zipcode:
                zipcodes.add(church.zipcode)
        if len(zipcodes) == 0:
            context = None
        elif len(cities) == 1 and len(zipcodes) == 1:
            context = f'{zipcodes.pop()} {cities.pop()}'
        else:
            context = get_departments_context(zipcodes)

        return AutocompleteResult(
            type='parish',
            name=parish.name,
            context=context,
            website_uuid=parish.website.uuid,
        )

    @classmethod
    def from_church(cls, church: Church) -> 'AutocompleteResult':
        if not church.zipcode:
            context = None
        elif church.city and church.zipcode:
            context = f'{church.zipcode} {church.city}'
        else:
            context = get_departments_context({church.zipcode})

        return AutocompleteResult(
            type='church',
            name=church.name,
            context=context,
            website_uuid=church.parish.website.uuid,
        )


def get_data_gouv_response(query) -> list[AutocompleteResult]:
    url = f'https://api-adresse.data.gouv.fr/search/'
    response = requests.get(url, params={
        'q': query,
        'limit': MAX_AUTOCOMPLETE_RESULTS,
        'autocomplete': 1,
        'type': 'municipality',
    })
    data = response.json()
    if 'features' not in data or not data['features']:
        return []

    results = []
    for result in data['features']:
        results.append(AutocompleteResult(
            type='municipality',
            name=result['properties']['name'],
            context=result['properties']['context'],
            latitude=result['geometry']['coordinates'][1],
            longitude=result['geometry']['coordinates'][0],
        ))

    return results


def get_parish_by_name_response(query) -> list[AutocompleteResult]:
    query_term = unhyphen_content(normalize_content(query))
    parishes = Parish.objects.annotate(
        search_name=Replace(Unaccent(Lower('name')), Value('-'), Value(' '))
    ).filter(website__is_active=True, search_name__contains=query_term)[:MAX_AUTOCOMPLETE_RESULTS]

    return list(map(AutocompleteResult.from_parish, parishes))


def get_church_by_name_response(query) -> list[AutocompleteResult]:
    query_term = unhyphen_content(normalize_content(query))
    churches = Church.objects.annotate(
        search_name=Replace(Unaccent(Lower('name')), Value('-'), Value(' '))
    ).filter(is_active=True, parish__website__is_active=True,
             search_name__contains=query_term)[:MAX_AUTOCOMPLETE_RESULTS]

    return list(map(AutocompleteResult.from_church, churches))


def sort_results(query, results: list[AutocompleteResult]) -> list[AutocompleteResult]:
    if not results:
        return []

    tuples = zip(map(lambda r: get_string_similarity(query, r.name), results), results)
    sorted_tuples = sorted(tuples, key=lambda t: t[0], reverse=True)
    _, sorted_values = zip(*sorted_tuples)

    return sorted_values


def get_aggregated_response(query) -> list[AutocompleteResult]:
    # TODO async call
    data_gouv_results = get_data_gouv_response(query)
    parish_by_name_results = get_parish_by_name_response(query)
    church_by_name_results = get_church_by_name_response(query)

    sorted_results = sort_results(
        query, data_gouv_results + parish_by_name_results + church_by_name_results)

    return sorted_results[:MAX_AUTOCOMPLETE_RESULTS]
