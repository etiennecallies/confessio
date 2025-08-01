from scraping.utils.enum_utils import StringEnum


class TagV2(StringEnum):
    SCHEDULE = 'schedule'
    SPECIFIER = 'specifier'


class EventMotion(StringEnum):
    START = 'start'
    SHOW = 'show'
    HIDE = 'hide'
    STOP = 'stop'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]
