from abc import abstractmethod
from uuid import UUID

from scraping.prune.models import Action, Source


class BaseActionInterface:
    @abstractmethod
    def get_action(self, line_without_link: str) -> tuple[Action, Source | None, UUID | None]:
        pass


class DummyActionInterface(BaseActionInterface):
    def get_action(self, line_without_link: str) -> tuple[Action, Source | None, UUID | None]:
        return Action.START, None, None
