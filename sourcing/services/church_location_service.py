from typing import Optional

from django.contrib.gis.geos import Point
from django.db.models.functions import Now

from home.models import ChurchModeration, Church, ExternalSource
from sourcing.utils.google_maps_api_utils import google_maps_geocode
from sourcing.utils.wikidata_utils import get_church_by_messesinfo_id


def compute_church_coordinates(
        church: Church, source: ExternalSource, no_save: bool = False
) -> tuple[Optional[Church], list[tuple[ChurchModeration.Category, bool]]]:
    wikidata_results = get_church_by_messesinfo_id(church.messesinfo_id)
    if wikidata_results and len(wikidata_results) == 1 and wikidata_results[0].coordinates_latlon:
        result = wikidata_results[0]
        church.wikidata_id = result.q_number
    else:
        result = google_maps_geocode(church.name, church.city, church.zipcode)

    categories = []
    if not result or not result.coordinates_latlon:
        categories.append((ChurchModeration.Category.LOCATION_NULL, False))
    else:
        categories.append((ChurchModeration.Category.LOCATION_FROM_API, False))
        latitude, longitude = result.coordinates_latlon
        church.location = Point(longitude, latitude)
        if not church.address:
            church.address = result.address
        if not church.zipcode:
            church.zipcode = result.zipcode
        if not church.city:
            church.city = result.city

    church_with_same_location = get_church_with_same_location(church)
    if church_with_same_location:
        # We can not save church since another church already has the same location
        add_church_location_conflict(church_with_same_location, church, source)
        return None, []

    if no_save:
        categories.append((ChurchModeration.Category.LOCATION_DIFFERS, True))
        return church, categories

    church.save()
    for category, validated in categories:
        add_church_moderation_if_not_exists(church, category, source, validated=validated)

    return church, categories


def add_church_moderation_if_not_exists(church: Church, category: ChurchModeration.Category,
                                        source: ExternalSource, validated: bool = False):
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
            validated_at=Now() if validated else None,
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
