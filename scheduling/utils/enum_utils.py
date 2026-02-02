from enum import Enum


class StringEnum(str, Enum):
    @classmethod
    def list_items(cls) -> list['StringEnum']:
        return [item for item in cls]


class BooleanStringEnum(StringEnum):
    TRUE = 'true'
    FALSE = 'false'

    @classmethod
    def from_bool(cls, value: bool) -> 'BooleanStringEnum':
        return cls.TRUE if value else cls.FALSE

    def to_bool(self) -> bool:
        return self == self.TRUE
