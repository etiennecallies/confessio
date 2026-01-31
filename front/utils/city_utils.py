def get_municipality_name(city: str, zipcode: str) -> str:
    if city.lower() in [
        'paris',
        'lyon',
        'marseille',
    ]:
        return f'{city} {get_arrondissement_from_zipcode(zipcode)}'

    return f'{city} ({zipcode})'


def get_arrondissement_from_zipcode(zipcode: str) -> str:
    return zipcode[3:5]


if __name__ == '__main__':
    print(get_municipality_name('Paris', '75001'))  # Paris 01
    print(get_municipality_name('Bordeaux', '33000'))  # Bordeaux (33000)
