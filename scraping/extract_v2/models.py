from scraping.utils.enum_utils import StringEnum


class TemporalTag(StringEnum):
    SCHEDULE = 'schedule'
    SPECIFIER = 'specifier'


class Temporal(StringEnum):
    NONE = 'none'
    SCHED = 'sched'
    SPEC = 'spec'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class EventMotion(StringEnum):
    START = 'start'
    HOLD = 'hold'
    HIDE = 'hide'
    STOP = 'stop'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]
