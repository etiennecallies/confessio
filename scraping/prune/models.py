from enum import Enum


class Action(str, Enum):
    SHOW = "show"
    HIDE = "hide"
    STOP = "stop"


class Source(str, Enum):
    HUMAN = "human"
    ML = "ml"
