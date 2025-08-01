from abc import abstractmethod

from scraping.extract_v2.models import TagV2, EventMotion
from scraping.extract_v2.tag_line import get_tags_with_regex, \
    get_event_motion_with_regex


class BaseQualifyLineInterface:
    @abstractmethod
    def get_tags_and_event_motion(self, stringified_line: str) -> tuple[set[TagV2], EventMotion]:
        pass


class RegexQualifyLineInterface(BaseQualifyLineInterface):
    def get_tags_and_event_motion(self, stringified_line: str) -> tuple[set[TagV2], EventMotion]:
        return get_tags_with_regex(stringified_line), get_event_motion_with_regex(stringified_line)
