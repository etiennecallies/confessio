import os

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel


class TrouverUneMesseLocation(BaseModel):
    latitude: float
    longitude: float


class TrouverUneMesseChurch(BaseModel):
    id: str
    name: str
    canonical_slug: str
    commune: str | None
    code_postal: str | None
    street: str | None
    location: TrouverUneMesseLocation


def fetch_trouverunemesse(url: str) -> dict | None:
    trouverunemesse_api_key = os.getenv("TROUVERUNEMESSE_API_KEY")

    headers = {'X-API-Key': trouverunemesse_api_key}
    try:
        response = httpx.get(url, headers=headers)
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

    return TrouverUneMesseChurch(**data)


def post_new_update_on_trouverunemesse(trouverunemesse_church: TrouverUneMesseChurch,
                                       comments: str) -> None:
    trouverunemesse_api_key = os.getenv("TROUVERUNEMESSE_API_KEY")
    url = 'https://api.trouverunemesse.fr/locality-update-requests/'

    headers = {'X-API-Key': trouverunemesse_api_key}
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
    except httpx.HTTPStatusError as e:
        print(f"Trouverunemesse POST API HTTP error: {e}")


if __name__ == '__main__':
    load_dotenv()
    print(fetch_trouverunemesse_by_messesinfo_id('75/paris-04/cathedrale-notre-dame-de-paris'))
