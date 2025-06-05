import os
from datetime import datetime

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel


class TrouverUneMesseLocation(BaseModel):
    latitude: float
    longitude: float


class TrouverUneMesseChurch(BaseModel):
    id: str
    name: str
    slug: str
    commune: str | None
    code_postal: str | None
    street: str | None = None
    location: TrouverUneMesseLocation


def get_headers() -> dict:
    trouverunemesse_api_key = os.getenv("TROUVERUNEMESSE_API_KEY")
    return {'X-API-Key': trouverunemesse_api_key}


def fetch_trouverunemesse(url: str) -> dict | None:
    try:
        response = httpx.get(url, headers=get_headers())

        if response.status_code == 404:
            print(f'Found 404 for URL: {url}')
            return None

        response.raise_for_status()
        data = response.json()

        if not data:
            return None

        return data

    except httpx.HTTPStatusError as e:
        print(f"Trouverunemesse GET API HTTP error: {e}")
        return None


def fetch_trouverunemesse_by_messesinfo_id(messesinfo_id: str) -> TrouverUneMesseChurch | None:
    """
    https://api.trouverunemesse.fr/redoc#tag/localities/operation/get_locality_from_messesinfo_localities_messes_info__messes_info_path__get
    """
    url = f'https://api.trouverunemesse.fr/localities/messes-info/{messesinfo_id}'
    data = fetch_trouverunemesse(url)
    if not data or not data['canonical_slug']:
        return None

    return fetch_trouverunemesse_by_slug(data['canonical_slug'])


def fetch_trouverunemesse_by_slug(trouverunemesse_slug: str) -> TrouverUneMesseChurch | None:
    """
    https://api.trouverunemesse.fr/redoc#tag/localities/operation/get_locality_details_locality_slugs__slug__get
    """
    url = f'https://api.trouverunemesse.fr/locality-slugs/{trouverunemesse_slug}?fields=location'

    data = fetch_trouverunemesse(url)
    if not data:
        return None

    if 'canonical_slug' in data:
        data['slug'] = data.pop('canonical_slug')

    return TrouverUneMesseChurch(**data)


def fetch_by_last_update(min_last_update: datetime | None = None, page: int = 1
                         ) -> list[TrouverUneMesseChurch]:
    url = f'https://api.trouverunemesse.fr/localities/by_last_update_date?page={page}'
    if min_last_update:
        url += f'&min_last_update={min_last_update.isoformat()}'
    data = fetch_trouverunemesse(url)
    if not data:
        return []

    return [TrouverUneMesseChurch(**item) for item in data['data']]


def authenticate_trouverunemesse() -> str | None:
    trouverunemesse_username = os.getenv("TROUVERUNEMESSE_USERNAME")
    trouverunemesse_password = os.getenv("TROUVERUNEMESSE_PASSWORD")
    print(f"Authenticating with trouverunemesse.fr as {trouverunemesse_username}")
    url = 'https://api.trouverunemesse.fr/auth/token'

    try:
        response = httpx.post(url, headers=get_headers(), json={
            "username": trouverunemesse_username,
            "password": trouverunemesse_password
        })

        if response.status_code != 200:
            print(response.status_code, response.text)

        response.raise_for_status()
        response_data = response.json()
        token = response_data['token']
        return token
    except httpx.HTTPStatusError as e:
        print(f"Trouverunemesse POST API HTTP error: {e}")
        return None


def post_new_update_on_trouverunemesse(trouverunemesse_church: TrouverUneMesseChurch,
                                       comments: str) -> None:
    token = authenticate_trouverunemesse()
    if not token:
        print("Authentication failed, cannot post update.")
        return

    headers = get_headers()
    headers['Authorization'] = f'Bearer {token}'
    url = 'https://api.trouverunemesse.fr/locality-update-requests/'
    try:
        response = httpx.post(url, headers=headers, json={
            "locality_id": trouverunemesse_church.id,
            "name": trouverunemesse_church.name,
            "location": {
                "latitude": trouverunemesse_church.location.latitude,
                "longitude": trouverunemesse_church.location.longitude
            },
            "complement": None,
            "comments": comments
        })
        response.raise_for_status()
        print(f"Successfully posted update for {trouverunemesse_church.name} on trouverunemesse.fr")
    except httpx.HTTPStatusError as e:
        print(f"Trouverunemesse POST API HTTP error: {e}")


if __name__ == '__main__':
    load_dotenv()
    print(fetch_trouverunemesse_by_messesinfo_id('75/paris-04/cathedrale-notre-dame-de-paris'))
