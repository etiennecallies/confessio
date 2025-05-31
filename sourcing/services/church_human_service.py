from home.models import ChurchModeration, Church


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
