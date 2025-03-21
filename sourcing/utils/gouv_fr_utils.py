from urllib.parse import quote

import requests
from pydantic import BaseModel
from requests import RequestException


class GouvFrGeocodingResult(BaseModel):
    coordinates_latlon: tuple[float, float] | None
    address: str | None
    city: str | None
    zipcode: str | None


def geocode_gouv_fr(name, address, city, zipcode) -> GouvFrGeocodingResult | None:
    query = f"q={quote(f'{name} {address} {city}')}"
    if zipcode:
        query += f'&postcode={zipcode}'

    url = f'https://api-adresse.data.gouv.fr/search/?{query}'

    try:
        print('geocoding with url', url)
        r = requests.get(url)
    except RequestException as e:
        print(e)
        return None

    if r.status_code != 200:
        print(r.status_code)
        print(r.text)
        return None

    data = r.json()
    if 'features' not in data or not data['features']:
        print('got no geocoding results', data)
        return None

    feature = data['features'][0]
    coordinates = feature.get('geometry', {}).get('coordinates', None)
    coordinates_latlon = (coordinates[1], coordinates[0]) if coordinates else None
    zipcode = feature.get('properties', {}).get('postcode', None)
    city = feature.get('properties', {}).get('city', None)
    address = feature.get('properties', {}).get('name', None)

    return GouvFrGeocodingResult(
        coordinates_latlon=coordinates_latlon,
        address=address,
        city=city,
        zipcode=zipcode
    )


if __name__ == '__main__':
    print(geocode_gouv_fr("Chapelle de l'école Saint-Joseph", "18 route d'Ecully",
                          "Dardilly", 69570))
