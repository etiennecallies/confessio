import json

import httpx


def fetch_oclocher_url(oclocher_url: str) -> list[dict]:
    timeout = httpx.Timeout(
        connect=10.0,
        read=30.0,
        write=10.0,
        pool=10.0
    )

    with httpx.Client(timeout=timeout) as client:
        try:
            resp = client.get(oclocher_url)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            print("Request failed:", e)
            raise


def fetch_organizations() -> list[dict]:
    url = f"https://api.oclocher.fr/organizations/"
    return fetch_oclocher_url(url)


def fetch_organization_locations(oclocher_organization_id: str) -> list[dict]:
    url = f"https://api.oclocher.fr/organizations/{oclocher_organization_id}/locations"
    return fetch_oclocher_url(url)


def fetch_organization_schedules(oclocher_organization_id: str):
    url = f"https://api.oclocher.fr/organizations/{oclocher_organization_id}/schedules"
    all_schedules = fetch_oclocher_url(url)

    # filter only confession
    return [
        schedule for schedule in all_schedules
        if schedule.get('selection') == 'confession'
    ]


if __name__ == '__main__':
    print(json.dumps(fetch_organization_schedules("ltkAShJzN8YHzl9FtxgD")))
    print(json.dumps(fetch_organization_locations("ltkAShJzN8YHzl9FtxgD")))
