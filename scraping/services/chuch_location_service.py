from home.models import ChurchModeration, Church, ExternalSource
from scraping.utils.geocode_address import geocode
from django.contrib.gis.geos import Point


def compute_church_coordinates(church: Church, source: ExternalSource):
    result = geocode(church.name, church.address, church.city, church.zipcode)
    if not result or not result.get('coordinates', None):
        category = ChurchModeration.Category.LOCATION_NULL
    else:
        longitude, latitude = result.get('coordinates')
        church.location = Point(longitude, latitude)
        if not church.address:
            church.address = result.get('address', None)
        if not church.zipcode:
            church.zipcode = result.get('zipcode', None)
        if not church.city:
            church.city = result.get('city', None)
        church.save()
        category = ChurchModeration.Category.LOCATION_FROM_API

    church_moderation = ChurchModeration(
        church=church,
        category=category,
        source=source,
        location=church.location
    )
    church_moderation.save()


