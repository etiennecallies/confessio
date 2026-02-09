from scheduling.utils.enum_utils import StringEnum


class Action(StringEnum):
    START = "start"
    SHOW = "show"
    HIDE = "hide"
    STOP = "stop"

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class Source(StringEnum):
    HUMAN = "human"
    ML = "ml"

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]
