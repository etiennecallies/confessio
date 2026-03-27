from front.utils.department_utils import get_department
from registry.models import Church, Diocese


def get_timezone_of_zipcode(zipcode: str) -> str:
    department = get_department(zipcode)
    if len(department) == 2:
        return 'Europe/Paris'

    if department == "971":
        return "America/Guadeloupe"
    if department == "972":
        return "America/Martinique"
    if department == "973":
        return "America/Cayenne"
    if department == "974":
        return "Indian/Reunion"
    if department == "975":
        return "America/Miquelon"
    if department == "976":
        return "Indian/Mayotte"

    raise ValueError(f"get_timezone_of_zipcode not implemented for department {department}")


def get_timezone_of_churches(churches: list[Church]) -> str | None:
    count_per_timezone = {}
    for church in churches:
        if church.zipcode:
            timezone = get_timezone_of_zipcode(church.zipcode)
            if timezone not in count_per_timezone:
                count_per_timezone[timezone] = 0
            count_per_timezone[timezone] += 1

    if not count_per_timezone:
        return None

    return max(count_per_timezone, key=count_per_timezone.get)


def get_diocese_timezone(diocese: Diocese) -> str:
    diocese_churches = [c for p in diocese.parishes.all() for c in p.churches.all()]
    return get_timezone_of_churches(diocese_churches)


def get_website_timezone(website_churches: list[Church]) -> str:
    timezone = get_timezone_of_churches(website_churches)
    if timezone:
        return timezone

    return get_diocese_timezone(website_churches[0].parish.diocese)


def get_timezone_of_church(church: Church) -> str:
    if church.zipcode:
        return get_timezone_of_zipcode(church.zipcode)

    return get_diocese_timezone(church.parish.diocese)
