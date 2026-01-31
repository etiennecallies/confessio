def get_desc_by_id(desc_list: list[str]) -> dict[int, str]:
    desc_by_id = {}
    for i, desc in enumerate(sorted(desc_list)):
        desc_by_id[i] = desc

    return desc_by_id


def group_consecutive_indices(n: int, indices: list[int]) -> list[tuple[bool, list[int]]]:
    result = []

    current_belongs = None
    current_indices = []
    for i in range(n):
        belongs = i in indices

        if current_belongs is None:
            current_belongs = belongs

        if current_belongs == belongs:
            current_indices.append(i)
        else:
            # Save the current group and start a new one
            result.append((current_belongs, current_indices))
            current_belongs = belongs
            current_indices = [i]

    # Append the last group
    if current_indices:
        result.append((current_belongs, current_indices))

    return result


def enumerate_with_and(items: list[str]) -> str:
    """
    >>> enumerate_with_and(['a', 'b', 'c'])
    'a, b and c'
    >>> enumerate_with_and(['a', 'b'])
    'a and b'
    >>> enumerate_with_and(['a'])
    'a'
    >>> enumerate_with_and([])
    ''
    """
    if not items:
        return ''

    if len(items) == 1:
        return items[0]

    return ', '.join(items[:-1]) + ' et ' + items[-1]


def round_robin(lst, n):
    return [lst[i::n] for i in range(n)]


def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
