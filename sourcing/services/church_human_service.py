from home.models import ChurchModeration, Church, ExternalSource
from sourcing.utils.trouverunemesse_utils import fetch_trouverunemesse_by_slug, \
    TrouverUneMesseLocation, post_new_update_on_trouverunemesse


def church_name_has_been_checked_by_human(church: Church) -> bool:
    for category in [
        ChurchModeration.Category.NAME_DIFFERS,
    ]:
        if ChurchModeration.objects.filter(
            church=church,
            category=category,
            validated_by_id__isnull=False,
        ).exists():
            return True
        if ChurchModeration.history.filter(
            church=church,
            category=category,
            history_user_id__isnull=False,
        ).exists():
            return True

    name = None
    for c in church.history.all():
        if c.name != name and c.history_user_id is not None:
            return True

        name = c.name

    return False


def church_location_has_been_checked_by_human(church: Church) -> bool:
    for category in [
        ChurchModeration.Category.LOCATION_NULL,
        ChurchModeration.Category.LOCATION_OUTLIER,
        ChurchModeration.Category.LOCATION_CONFLICT,
        ChurchModeration.Category.LOCATION_DIFFERS,
        ChurchModeration.Category.LOCATION_FROM_API,
    ]:
        if ChurchModeration.objects.filter(
            church=church,
            category=category,
            validated_by_id__isnull=False,
        ).exists():
            return True
        if ChurchModeration.history.filter(
            church=church,
            category=category,
            history_user_id__isnull=False,
        ).exists():
            return True

    location = None
    address = None
    zipcode = None
    city = None
    for c in church.history.all():
        if (c.location != location or c.address != address
                or c.zipcode != zipcode or c.city != city) and c.history_user_id is not None:
            return True

        location = c.location
        address = c.address
        zipcode = c.zipcode
        city = c.city

    return False


def on_church_human_validation(church_moderation: ChurchModeration) -> None:
    if church_moderation.source != ExternalSource.TROUVERUNEMESSE:
        return

    if church_moderation.category == ChurchModeration.Category.NAME_DIFFERS:
        if church_moderation.church.name == church_moderation.name:
            print("Name has taken external suggestion, not updating")
            return

    if church_moderation.category == ChurchModeration.Category.LOCATION_DIFFERS:
        if not church_moderation.location_desc_differs():
            print("Location has taken external suggestion, not updating")
            return

    if not church_moderation.church.trouverunemesse_slug:
        print("Trouverunemesse slug not found")
        return

    trouverunemesse_church = fetch_trouverunemesse_by_slug(
        church_moderation.church.trouverunemesse_slug
    )
    if not trouverunemesse_church:
        print("Trouverunemesse church not found")
        return

    if church_moderation.category == ChurchModeration.Category.NAME_DIFFERS:
        if trouverunemesse_church.name != church_moderation.name:
            print("Name has changed in the meantime, not updating")
            return

        trouverunemesse_church.name = church_moderation.church.name
    if church_moderation.category == ChurchModeration.Category.LOCATION_DIFFERS:
        if trouverunemesse_church.location.latitude != church_moderation.location.y \
                or trouverunemesse_church.location.longitude != church_moderation.location.x \
                or trouverunemesse_church.street != church_moderation.address \
                or trouverunemesse_church.code_postal != church_moderation.zipcode \
                or trouverunemesse_church.commune != church_moderation.city:
            print("Location has changed in the meantime, not updating")
            return
        trouverunemesse_church.location = TrouverUneMesseLocation(
            latitude=church_moderation.church.location.y,
            longitude=church_moderation.church.location.x
        )
        trouverunemesse_church.street = church_moderation.church.address
        trouverunemesse_church.code_postal = church_moderation.church.zipcode
        trouverunemesse_church.commune = church_moderation.church.city

    post_new_update_on_trouverunemesse(trouverunemesse_church)
