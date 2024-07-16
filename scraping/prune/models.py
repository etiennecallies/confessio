from enum import Enum


class Action(str, Enum):
    SHOW = "show"
    HIDE = "hide"
    STOP = "stop"
