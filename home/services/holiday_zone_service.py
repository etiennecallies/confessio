from home.models import Website
from scraping.parse.holidays import HolidayZoneEnum


def get_website_holiday_zone(website: Website) -> HolidayZoneEnum:
    # TODO
    return HolidayZoneEnum.FR_ZONE_A
