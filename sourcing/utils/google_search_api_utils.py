import os

import requests
from pydantic import BaseModel


class GoogleApiResult(BaseModel):
    title: str
    link: str
    display_link: str
    formatted_url: str
    snippet: str


def get_google_search_results(query: str) -> list[GoogleApiResult]:
    # PSE stands for Programmable Search Engine
    google_pse_id = os.getenv("GOOGLE_PSE_ID")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'key': google_api_key,
        'cx': google_pse_id,
        'q': query
    }
    response = requests.get(url, params=params)
    results = response.json()
    if 'items' not in results or not results['items']:
        return []

    items = []
    for item in results['items']:
        items.append(GoogleApiResult(
            title=item['title'],
            link=item['link'],
            display_link=item['displayLink'],
            formatted_url=item['formattedUrl'],
            snippet=item['snippet']
        ))

    return items


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    print(get_google_search_results("paroisse st michel le havre"))
