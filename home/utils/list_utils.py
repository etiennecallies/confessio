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


def split_list(lst, n):
    q, r = divmod(len(lst), n)  # Quotient and remainder
    return [lst[i * q + min(i, r):(i + 1) * q + min(i + 1, r)] for i in range(n)]
