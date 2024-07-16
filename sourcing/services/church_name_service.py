from home.models import Church
from sourcing.utils.string_utils import get_string_similarity


def sort_by_name_similarity(church: Church, churches: list[Church]) -> list[Church]:
    if not churches:
        return []

    similarity_tuples = zip(map(lambda p: get_string_similarity(church.name, p.name), churches),
                            churches)

    # keep only the most three similar churches
    closest_churches = sorted(similarity_tuples, key=lambda t: t[0], reverse=True)
    _, similar_churches = zip(*closest_churches)

    return similar_churches
