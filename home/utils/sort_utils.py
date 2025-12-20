def compare_int_or_none_tuples(a: tuple[int | None, ...], b: tuple[int | None, ...]) -> bool:
    """
    Compare two tuples of integers or None values.

    None is considered less than any integer.

    Returns:
        -1 if a < b
         0 if a == b
         1 if a > b
    """
    for val_a, val_b in zip(a, b):
        if val_a is None and val_b is None:
            continue
        if val_a is None:
            return True
        if val_b is None:
            return False
        if val_a < val_b:
            return True
        if val_a > val_b:
            return False
    return len(a) < len(b)
