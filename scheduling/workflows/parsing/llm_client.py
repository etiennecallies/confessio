from abc import abstractmethod
from enum import Enum
from typing import Optional

from scheduling.workflows.parsing.schedules import SchedulesList


class LLMProvider(str, Enum):
    OPENAI = "openai"

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class LLMClientInterface:
    @abstractmethod
    async def get_completions(self,
                              messages: list[dict],
                              temperature: float) -> tuple[Optional[SchedulesList], Optional[str]]:
        pass

    @abstractmethod
    def get_provider(self) -> LLMProvider:
        pass

    @abstractmethod
    def get_model(self) -> str:
        pass
