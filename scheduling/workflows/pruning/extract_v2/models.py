from scheduling.utils.enum_utils import StringEnum


class Temporal(StringEnum):
    NONE = 'none'
    SCHED = 'sched'
    SPEC = 'spec'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class EventMention(StringEnum):
    EVENT = 'event'
    NEUTRAL = 'neutral'
    OTHER = 'other'

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]
