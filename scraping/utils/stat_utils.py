from scipy import stats


def is_significantly_different(accuracy1, accuracy2, n1, n2):
    if n1 == 0 or n2 == 0:
        return False

    nb_success1 = round(n1 * accuracy1)
    values1 = [1] * nb_success1 + [0] * (n1 - nb_success1)

    nb_success2 = round(n2 * accuracy2)
    values2 = [1] * nb_success2 + [0] * (n2 - nb_success2)
    t_stat, p_value = stats.ttest_ind(values1, values2)
    print(f"p_value: {p_value}")

    return p_value < 0.05


if __name__ == '__main__':
    print(is_significantly_different(0.875, 0.915, 400, 800))
