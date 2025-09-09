from uuid import UUID

from pydantic import BaseModel

from scraping.extract_v2.models import TagV2, EventMotion
from scraping.extract_v2.qualify_line_interfaces import BaseQualifyLineInterface
from scraping.refine.refine_content import stringify_html
from scraping.utils.html_utils import split_lines


class LineAndTagV2(BaseModel):
    line: str
    stringified_line: str
    tags: set[TagV2]
    event_motion: EventMotion
    is_default_hold: bool
    sentence_uuid: UUID | None


def split_and_tag_v2(refined_content: str, qualify_line_interface: BaseQualifyLineInterface
                     ) -> list[LineAndTagV2]:
    results = []

    # Split into lines (or <table>)
    for line in split_lines(refined_content):
        results.append(create_line_and_tag_v2(line, qualify_line_interface))

    return results


def create_line_and_tag_v2(line: str, qualify_line_interface: BaseQualifyLineInterface
                           ) -> LineAndTagV2:
    stringified_line = stringify_html(line)

    tags, event_motion, is_default_hold, sentence_uuid = \
        qualify_line_interface.get_tags_and_event_motion(stringified_line)

    return LineAndTagV2(
        line=line,
        stringified_line=stringified_line,
        tags=tags,
        event_motion=event_motion,
        is_default_hold=is_default_hold,
        sentence_uuid=sentence_uuid,
    )
