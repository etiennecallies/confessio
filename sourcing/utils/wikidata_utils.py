import requests
from pydantic import BaseModel


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


class WikidataResult(BaseModel):
    q_number: str
    label: str
    coordinates_latlon: tuple[float, float] | None
    address: str | None
    city: str | None
    zipcode: str | None


def get_church_by_messesinfo_id(messesinfo_id: str | None
                                ) -> list[WikidataResult]:
    if not messesinfo_id:
        print("Cannot retrieve church on wikidata since no messesinfo_id provided")
        return []

    print(f"Retrieving church on wikidata with messesinfo_id: {messesinfo_id}")

    endpoint_url = "https://query.wikidata.org/sparql"

    # SPARQL query to find entity by field value
    query = f"""
    SELECT
        ?item
        ?itemLabel
        ?coordinates
        ?streetLabel
        ?houseNumber
        ?streetAddress
        ?cityLabel
        ?postalCode
    WHERE
    {{
        ?item wdt:P1644 "{messesinfo_id}".
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],fr". }}
        OPTIONAL {{ ?item wdt:P625 ?coordinates. }}
        OPTIONAL {{ ?item wdt:P669 ?street. }}
        OPTIONAL {{ ?item p:P669 ?streetStatement.
               ?streetStatement pq:P670 ?houseNumber. }}
        OPTIONAL {{ ?item wdt:P6375 ?streetAddress. }}
        OPTIONAL {{ ?item wdt:P131 ?city. }}
        OPTIONAL {{ ?city wdt:P281 ?postalCode. }}
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

            street_label = r['streetLabel']['value'] if 'streetLabel' in r else None
            house_number = r['houseNumber']['value'] if 'houseNumber' in r else None
            full_address = f'{house_number} {street_label}' if house_number else street_label
            street_address = r['streetAddress']['value'] if 'streetAddress' in r else None

            city = r['cityLabel']['value'] if 'cityLabel' in r else None
            zipcode = r['postalCode']['value'] if 'postalCode' in r else None

            coordinates = None
            if 'coordinates' in r:
                coordinates = extract_coordinates(r['coordinates']['value'])

            wikidata_result = WikidataResult(
                q_number=q_number,
                label=r['itemLabel']['value'],
                coordinates_latlon=coordinates,
                address=full_address or street_address,
                city=city,
                zipcode=zipcode
            )
            results.append(wikidata_result)

        return results

    except requests.RequestException as e:
        print(f"Error querying Wikidata: {e}")
        return []


# Example usage
if __name__ == "__main__":
    # result = get_church_by_messesinfo_id('78/chapet/saint-denis')
    result = get_church_by_messesinfo_id('35/parigne/chapelle-saint-roch')
    # result = get_church_by_messesinfo_id('69/lyon-05/basilique-notre-dame-de-fourviere')
    # result = get_church_by_messesinfo_id('63/busseol/eglise')
    # result = get_church_by_messesinfo_id('49/saint-georges-des-sept-voies/eglise')
    # result = get_church_by_messesinfo_id('78/boissy-sans-avoir/saint-sebastien')
    for v in result:
        print(result)
