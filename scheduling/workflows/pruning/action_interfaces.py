from abc import abstractmethod
from uuid import UUID

from scheduling.workflows.pruning.models import Action, Source


class BaseActionInterface:
    @abstractmethod
    def get_action(self, stringified_line: str) -> tuple[Action, Source | None, UUID | None]:
        pass


class DummyActionInterface(BaseActionInterface):
    def get_action(self, stringified_line: str) -> tuple[Action, Source | None, UUID | None]:
        return Action.START, None, None
