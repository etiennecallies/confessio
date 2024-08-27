from difflib import SequenceMatcher


def get_string_similarity(query, name: str) -> float:
    return SequenceMatcher(None, query, name).ratio()
