import os
from urllib.parse import quote

import requests
from pydantic import BaseModel
from requests import RequestException


class GoogleMapsGeocodingResult(BaseModel):
    coordinates_latlon: tuple[float, float] | None
    address: str | None
    city: str | None
    zipcode: str | None


def extract_address_component(result, component_type):
    components = result.get('address_components', [])
    for component in components:
        if component_type in component['types']:
            return component['long_name']

    return None


def google_maps_geocode(name, city, zipcode) -> GoogleMapsGeocodingResult | None:
    query = f"{quote(f'{name} {zipcode} {city}')}"

    google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    base_url = 'https://maps.googleapis.com/maps/api/geocode/json'

    url = f'{base_url}?address={query}&key={google_maps_api_key}'

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
    if 'results' not in data or not data['results']:
        print('got no geocoding results', data)
        return None

    result = data['results'][0]
    coordinates = result.get('geometry', {}).get('location', None)
    coordinates_latlon = (coordinates['lat'], coordinates['lng']) if coordinates else None
    zipcode = extract_address_component(result, 'postal_code')
    city = extract_address_component(result, 'locality')
    route = extract_address_component(result, 'route')
    street_number = extract_address_component(result, 'street_number')
    address = f'{street_number} {route}' if street_number else route

    return GoogleMapsGeocodingResult(
        coordinates_latlon=coordinates_latlon,
        address=address,
        city=city,
        zipcode=zipcode
    )


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    print(google_maps_geocode("Chapelle de l'école Saint-Joseph", "Dardilly", 69570))
