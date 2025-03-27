from django.contrib.gis.geos import Point
from haversine import haversine, Unit


def get_geo_distance(p1: Point, p2: Point):
    return haversine(p1, p2, unit=Unit.METERS)


def get_barycenter_minus_point(barycenter: Point, point: Point, n: int) -> Point:
    return Point((barycenter.x * n - point.x) / (n - 1),
                 (barycenter.y * n - point.y) / (n - 1))


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
