import json
from dataclasses import dataclass
from typing import Optional

import requests

from home.models import Parish


MAX_AUTOCOMPLETE_RESULTS = 15


@dataclass
class AutocompleteResult:
    type: str
    name: str
    context: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


def get_data_gouv_response(query) -> list[AutocompleteResult]:
    url = f'https://api-adresse.data.gouv.fr/search/'
    response = requests.get(url, params={
        'q': query,
        'limit': MAX_AUTOCOMPLETE_RESULTS,
        'autocomplete': 1,
        'type': 'municipality',
    })
    data = response.json()
    print(json.dumps(data))
    if 'features' not in data or not data['features']:
        return []

    results = []
    for result in data['features']:
        print(result)
        results.append(AutocompleteResult(
            type='municipality',
            name=result['properties']['name'],
            context=result['properties']['context'],
            latitude=result['geometry']['coordinates'][1],
            longitude=result['geometry']['coordinates'][0],
        ))

    return results


def get_parish_by_name_response(query) -> list[AutocompleteResult]:
    parishes = Parish.objects.filter(is_active=True, name__contains=query)\
        [:MAX_AUTOCOMPLETE_RESULTS]

    results = []
    for parish in parishes:
        results.append(AutocompleteResult(
            type='parish',
            name=parish.name,
            context=parish.name,  # TODO find dominant department
        ))

    return results


def get_aggreagated_response(query) -> list[AutocompleteResult]:
    # TODO async call
    data_gouv_results = get_data_gouv_response(query)
    parish_by_name_results = get_parish_by_name_response(query)

    # TODO merge and sort
    return data_gouv_results + parish_by_name_results
