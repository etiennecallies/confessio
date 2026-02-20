from front.utils.department_utils import get_department
from registry.models import Church


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
    if department == "976":
        return "Indian/Mayotte"

    raise ValueError(f"get_timezone_of_zipcode not implemented for department {department}")


def get_timezone_of_churches(churches: list[Church]) -> str:
    count_per_timezone = {}
    for church in churches:
        if church.zipcode:
            timezone = get_timezone_of_zipcode(church.zipcode)
            if timezone not in count_per_timezone:
                count_per_timezone[timezone] = 0
            count_per_timezone[timezone] += 1

    return max(count_per_timezone, key=count_per_timezone.get)
