from abc import abstractmethod
from uuid import UUID

from scheduling.workflows.pruning.extract_v2.models import Temporal, EventMention
from scheduling.workflows.pruning.extract_v2.tag_line import get_temporal_tags_with_regex, \
    get_event_mention_tags_with_regex


class BaseQualifyLineInterface:
    @abstractmethod
    def get_temporal_and_event_mention_tags(
            self, stringified_line: str) -> tuple[set[Temporal], set[EventMention], UUID | None]:
        pass


class RegexQualifyLineInterface(BaseQualifyLineInterface):
    def get_temporal_and_event_mention_tags(
            self, stringified_line: str) -> tuple[set[Temporal], set[EventMention], UUID | None]:
        return (get_temporal_tags_with_regex(stringified_line),
                get_event_mention_tags_with_regex(stringified_line),
                None)


class DummyQualifyLineInterface(BaseQualifyLineInterface):
    def get_temporal_and_event_mention_tags(
            self, stringified_line: str) -> tuple[set[Temporal], set[EventMention], UUID | None]:
        return set(), set(), None
