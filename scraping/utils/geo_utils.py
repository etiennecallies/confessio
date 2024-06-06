from django.contrib.gis.geos import Point
from haversine import haversine, Unit


def get_geo_distance(p1: Point, p2: Point):
    return haversine(p1, p2, unit=Unit.METERS)
