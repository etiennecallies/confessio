import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional

import requests

from home.models import Parish
from scraping.utils.department_utils import get_departments_context

MAX_AUTOCOMPLETE_RESULTS = 15


@dataclass
class AutocompleteResult:
    type: str
    name: str
    context: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    parish_uuid: Optional[str] = None

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
            context = ''
        elif len(cities) == 1 and len(zipcodes) == 1:
            context = f'{zipcodes.pop()} {cities.pop()}'
        else:
            context = get_departments_context(zipcodes)

        return AutocompleteResult(
            type='parish',
            name=parish.name,
            context=context,
            parish_uuid=parish.uuid,
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
    parishes = Parish.objects.filter(is_active=True, name__icontains=query)\
        [:MAX_AUTOCOMPLETE_RESULTS]

    return list(map(AutocompleteResult.from_parish, parishes))


def get_distance(query, result: AutocompleteResult) -> float:
    return SequenceMatcher(None, query, result.name).ratio()


def sort_results(query, results: list[AutocompleteResult]) -> list[AutocompleteResult]:
    if not results:
        return []

    tuples = zip(map(lambda r: get_distance(query, r), results), results)
    sorted_tuples = sorted(tuples, key=lambda t: t[0])
    _, sorted_values = zip(*sorted_tuples)

    return sorted_values


def get_aggreagated_response(query) -> list[AutocompleteResult]:
    # TODO async call
    data_gouv_results = get_data_gouv_response(query)
    parish_by_name_results = get_parish_by_name_response(query)

    sorted_results = sort_results(query, data_gouv_results + parish_by_name_results)

    return sorted_results[:MAX_AUTOCOMPLETE_RESULTS]
