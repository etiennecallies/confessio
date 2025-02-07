from typing import Optional

from home.models import ChurchModeration, Church, ExternalSource
from sourcing.utils.geocode_address import geocode
from django.contrib.gis.geos import Point


def compute_church_coordinates(church: Church, source: ExternalSource,
                               no_save: bool = False
                               ) -> tuple[Optional[Church], Optional[ChurchModeration.Category]]:
    result = geocode(church.name, church.address, church.city, church.zipcode)
    if not result or not result.get('coordinates', None):
        category = ChurchModeration.Category.LOCATION_NULL
    else:
        category = ChurchModeration.Category.LOCATION_FROM_API
        longitude, latitude = result.get('coordinates')
        church.location = Point(longitude, latitude)
        if not church.address:
            church.address = result.get('address', None)
        if not church.zipcode:
            church.zipcode = result.get('zipcode', None)
        if not church.city:
            church.city = result.get('city', None)

    church_with_same_location = get_church_with_same_location(church)
    if church_with_same_location:
        # We can not save church since another church already has the same location
        add_church_location_conflict(church_with_same_location, church, source)
        return None, None

    if no_save:
        return church, category

    church.save()
    add_church_moderation_if_not_exists(church, category, source)

    return church, category


def add_church_moderation_if_not_exists(church: Church, category: ChurchModeration.Category,
                                        source: ExternalSource):
    try:
        ChurchModeration.objects.get(
            church=church,
            category=category,
            source=source
        )
    except ChurchModeration.DoesNotExist:
        church_moderation = ChurchModeration(
            church=church,
            category=category,
            source=source,
            location=church.location,
            diocese=church.parish.diocese,
        )
        church_moderation.save()


def add_church_location_conflict(existing_church: Church, church: Church,
                                 source: ExternalSource):
    church_moderation = ChurchModeration(
        church=existing_church,
        category=ChurchModeration.Category.LOCATION_CONFLICT,
        source=source,
        name=church.name,
        address=church.address,
        zipcode=church.zipcode,
        city=church.city,
        messesinfo_id=church.messesinfo_id,
        diocese=existing_church.parish.diocese,
    )

    try:
        existing_moderation = ChurchModeration.objects.get(
            church=church_moderation.church,
            category=church_moderation.category,
            source=church_moderation.source
        )
        if existing_moderation.name != church_moderation.name:
            existing_moderation.delete()
            church_moderation.save()
    except ChurchModeration.DoesNotExist:
        church_moderation.save()


def get_church_with_same_location(church: Church) -> Optional[Church]:
    try:
        return Church.objects.filter(location=church.location).exclude(pk=church.pk).get()
    except Church.DoesNotExist:
        return None
