from enum import Enum


class Action(str, Enum):
    SHOW = "show"
    HIDE = "hide"
    STOP = "stop"

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class Source(str, Enum):
    HUMAN = "human"
    ML = "ml"

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]
