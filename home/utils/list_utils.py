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
