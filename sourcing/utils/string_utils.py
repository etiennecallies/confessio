from difflib import SequenceMatcher


def get_string_similarity(query, name: str) -> float:
    return SequenceMatcher(None, query, name).ratio()


def lower_first(s: str) -> str:
    return s[:1].lower() + s[1:] if s else ''


def city_and_prefix(city: str) -> str:
    if not city:
        return ''

    if len(city) < 3:
        return f'à {city}'

    if city[:3].lower() == 'le ':
        return f'au {city[3:]}'

    return f'à {city}'
