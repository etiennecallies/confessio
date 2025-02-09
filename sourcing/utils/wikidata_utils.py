import requests


def extract_coordinates(point_str: str) -> tuple[float, float] | None:
    """
    Convert a Wikidata Point string into a (latitude, longitude) tuple.
    Example: "Point(2.1892296 48.8091951)" -> (48.8091951, 2.1892296)

    Note: Wikidata stores coordinates as (longitude latitude) but returns
    them as (latitude, longitude) for conventional use.
    """
    if not point_str:
        return None

    # Remove "Point(" and ")" and split into longitude and latitude
    coords = point_str.strip('Point()').split()

    # Convert to floats and return in (latitude, longitude) order
    longitude = float(coords[0])
    latitude = float(coords[1])

    return latitude, longitude


def get_church_by_messesinfo_id(messesinfo_id: str
                                ) -> list[tuple[str, str, tuple[float, float] | None]]:
    endpoint_url = "https://query.wikidata.org/sparql"

    # SPARQL query to find entity by field value
    query = f"""
    SELECT ?item ?itemLabel ?coordinates
    WHERE
    {{
        ?item wdt:P1644 "{messesinfo_id}".
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],fr". }}
        OPTIONAL {{ ?item wdt:P625 ?coordinates. }}
    }}
    """

    try:
        # Set up the request with proper headers
        headers = {
            'User-Agent': 'Python Wikidata Query Script/1.0',
            'Accept': 'application/json'
        }

        # Make the request
        response = requests.get(
            endpoint_url,
            params={'query': query, 'format': 'json'},
            headers=headers
        )
        response.raise_for_status()  # Raise exception for bad status codes

        # Parse the response
        data = response.json()

        if not data['results']['bindings']:
            return []

        results = []
        for r in data['results']['bindings']:
            q_number = r['item']['value'].split('/')[-1]
            coordinates = None
            if 'coordinates' in r:
                coordinates = extract_coordinates(r['coordinates']['value'])
            results.append((q_number, r['itemLabel']['value'], coordinates))

        return results

    except requests.RequestException as e:
        print(f"Error querying Wikidata: {e}")
        return []


# Example usage
if __name__ == "__main__":
    result = get_church_by_messesinfo_id('78/chapet/saint-denis')
    # result = get_church_by_messesinfo_id('69/lyon-05/basilique-notre-dame-de-fourviere')
    for v in result:
        print(result)
