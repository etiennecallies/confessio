from abc import abstractmethod
from uuid import UUID

from scraping.prune.models import Action, Source


class BaseActionInterface:
    @abstractmethod
    def get_action(self, line_without_link: str) -> tuple[Action, Source | None, UUID | None]:
        pass


class DummyActionInterface(BaseActionInterface):
    def get_action(self, line_without_link: str) -> tuple[Action, Source | None, UUID | None]:
        return Action.SHOW, None, None


class KeyValueInterface(BaseActionInterface):
    def __init__(self, action_per_line_without_link: dict[str, Action]):
        self.action_per_line_without_link = action_per_line_without_link

    def get_action(self, line_without_link: str) -> tuple[Action, Source | None, UUID | None]:
        return self.action_per_line_without_link[line_without_link], Source.HUMAN, None
