from enum import Enum


class TagV2(str, Enum):
    SCHEDULE = 'schedule'
    SPECIFIER = 'specifier'


class EventMotion(str, Enum):
    START = 'start'
    SHOW = 'show'
    HIDE = 'hide'
    STOP = 'stop'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]
