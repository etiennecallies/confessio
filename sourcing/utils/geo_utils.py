from django.contrib.gis.geos import Point
from haversine import haversine, Unit


def lat_lon(point: Point) -> tuple[float, float]:
    return point.y, point.x


def get_geo_distance(p1: Point, p2: Point):
    return haversine(lat_lon(p1), lat_lon(p2), unit=Unit.METERS)


def get_barycenter_minus_point(barycenter: Point, point: Point, n: int) -> Point:
    return Point((barycenter.x * n - point.x) / (n - 1),
                 (barycenter.y * n - point.y) / (n - 1))


def check_coordinates_validity(point: Point) -> bool:
    return point.x is not None and point.y is not None and \
        -180 < point.x < 180 and -90 < point.y < 90


def get_distances_to_barycenter(points: list[Point]) -> dict[Point, float]:
    n = len(points)
    if n == 0:
        return {}

    if n == 1:
        return {points[0]: 0}

    barycenter = Point(
        sum([point.x for point in points]) / n,
        sum([point.y for point in points]) / n
    )
    return {p: get_geo_distance(p, get_barycenter_minus_point(barycenter, p, n))
            for p in points}
