from enum import Enum


class StringEnum(str, Enum):
    @classmethod
    def list_items(cls) -> list['StringEnum']:
        return [item for item in cls]
