from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]
