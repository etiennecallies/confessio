from home.models import Website, Diocese, Church
from home.utils.department_utils import get_department
from scraping.parse.holidays import HolidayZoneEnum, HOLIDAY_ZONE_PER_DEPARTMENT


def get_holiday_zone_of_churches(churches: list[Church]) -> HolidayZoneEnum | None:
    count_per_zone = {}
    for church in churches:
        if church.zipcode:
            department = get_department(church.zipcode)
            holiday_zone = HOLIDAY_ZONE_PER_DEPARTMENT[department]
            if holiday_zone not in count_per_zone:
                count_per_zone[holiday_zone] = 0
            count_per_zone[holiday_zone] += 1

    if not count_per_zone:
        return None

    return max(count_per_zone, key=count_per_zone.get)


def get_diocese_holiday_zone(diocese: Diocese) -> HolidayZoneEnum:
    diocese_churches = [c for p in diocese.parishes.all() for c in p.churches.all()]
    return get_holiday_zone_of_churches(diocese_churches)


def get_website_holiday_zone(website: Website, website_churches: list[Church]) -> HolidayZoneEnum:
    holiday_zone = get_holiday_zone_of_churches(website_churches)
    if holiday_zone:
        return holiday_zone

    return get_diocese_holiday_zone(website.get_diocese())
