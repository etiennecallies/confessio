from abc import abstractmethod
from enum import Enum
from typing import Optional

from scraping.parse.schedules import SchedulesList


class LLMProvider(str, Enum):
    OPENAI = "openai"
    MISTRAL = "mistral"

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class LLMClientInterface:
    @abstractmethod
    def get_completions(self,
                        messages: list[dict],
                        temperature: float) -> tuple[Optional[SchedulesList], Optional[str]]:
        pass

    @abstractmethod
    def get_provider(self) -> LLMProvider:
        pass

    @abstractmethod
    def get_model(self) -> str:
        pass
