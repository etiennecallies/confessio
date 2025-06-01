from django.contrib.gis.geos import Point

from home.models import Church, ChurchModeration, ExternalSource
from sourcing.services.church_human_service import church_location_has_been_checked_by_human
from sourcing.utils.trouverunemesse_utils import fetch_trouverunemesse_by_messesinfo_id


def add_church_moderation_if_not_exists(church_moderation: ChurchModeration):
    try:
        ChurchModeration.objects.get(
            church=church_moderation.church,
            category=church_moderation.category,
            source=church_moderation.source
        )
    except ChurchModeration.DoesNotExist:
        church_moderation.save()


def sync_trouverunemesse_for_church(church: Church):
    if church.trouverunemesse_slug:
        print(f"Church {church.name} already has a trouverunemesse_slug, skipping sync.")
        return None

    if not church.messesinfo_id:
        print(f"Church {church.name} does not have a messesinfo_id, skipping sync.")
        return None

    trouverunemesse_church = fetch_trouverunemesse_by_messesinfo_id(church.messesinfo_id)
    if not trouverunemesse_church:
        print(f"Could not find trouverunemesse church for messesinfo_id {church.messesinfo_id}")
        return None

    church.trouverunemesse_id = trouverunemesse_church.id
    church.trouverunemesse_slug = trouverunemesse_church.canonical_slug
    church.save()

    location_moderation_added = None
    name_moderation_added = None

    if church.location.y != trouverunemesse_church.location.latitude or \
            church.location.x != trouverunemesse_church.location.longitude or \
            church.address != trouverunemesse_church.street or \
            church.zipcode != trouverunemesse_church.code_postal or \
            church.city != trouverunemesse_church.commune:
        # we remove every non-validated moderation related to location
        ChurchModeration.objects.filter(
            church=church,
            category__in=[
                ChurchModeration.Category.LOCATION_NULL,
                ChurchModeration.Category.LOCATION_OUTLIER,
                ChurchModeration.Category.LOCATION_CONFLICT,
                ChurchModeration.Category.LOCATION_FROM_API
            ],
            validated_at__isnull=True,
        ).delete()

        if church_location_has_been_checked_by_human(church):
            add_church_moderation_if_not_exists(
                ChurchModeration(
                    church=church,
                    category=ChurchModeration.Category.LOCATION_DIFFERS,
                    source=ExternalSource.TROUVERUNEMESSE,
                    address=trouverunemesse_church.street,
                    zipcode=trouverunemesse_church.code_postal,
                    city=trouverunemesse_church.commune,
                    location=Point(trouverunemesse_church.location.longitude,
                                   trouverunemesse_church.location.latitude),
                    diocese=church.parish.diocese
                )
            )
            location_moderation_added = True
        else:
            church.location = Point(trouverunemesse_church.location.longitude,
                                    trouverunemesse_church.location.latitude)
            church.address = trouverunemesse_church.street
            church.zipcode = trouverunemesse_church.code_postal
            church.city = trouverunemesse_church.commune
            church.save()
            location_moderation_added = False

    # NAME is not of top quality for now
    # if church.name != trouverunemesse_church.name:
    #     if church_name_has_been_checked_by_human(church):
    #         add_church_moderation_if_not_exists(
    #             ChurchModeration(
    #                 church=church,
    #                 category=ChurchModeration.Category.NAME_DIFFERS,
    #                 source=ExternalSource.TROUVERUNEMESSE,
    #                 name=trouverunemesse_church.name,
    #                 diocese=church.parish.diocese
    #             )
    #         )
    #         name_moderation_added = True
    #     else:
    #         church.name = trouverunemesse_church.name
    #         church.save()
    #         name_moderation_added = False

    return location_moderation_added, name_moderation_added
