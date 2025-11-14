from abc import abstractmethod
from uuid import UUID

from scraping.extract_v2.models import TemporalTag, EventMotion
from scraping.extract_v2.tag_line import get_tags_with_regex, \
    get_event_motion_with_regex, get_is_default_hold_with_regex


class BaseQualifyLineInterface:
    @abstractmethod
    def get_tags_and_event_motion(self, stringified_line: str
                                  ) -> tuple[set[TemporalTag], EventMotion, bool, UUID | None]:
        pass


class RegexQualifyLineInterface(BaseQualifyLineInterface):
    def get_tags_and_event_motion(self, stringified_line: str
                                  ) -> tuple[set[TemporalTag], EventMotion, bool, UUID | None]:
        return (get_tags_with_regex(stringified_line),
                get_event_motion_with_regex(stringified_line),
                get_is_default_hold_with_regex(stringified_line),
                None)


class DummyQualifyLineInterface(BaseQualifyLineInterface):
    def get_tags_and_event_motion(self, stringified_line: str
                                  ) -> tuple[set[TemporalTag], EventMotion, bool, UUID | None]:
        return set(), EventMotion.START, False, None
