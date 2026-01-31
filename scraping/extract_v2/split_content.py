from uuid import UUID

from pydantic import BaseModel

from crawling.workflows.refine.refine_content import stringify_html
from scraping.extract_v2.models import Temporal, EventMention
from scraping.extract_v2.qualify_line_interfaces import BaseQualifyLineInterface
from scraping.utils.html_utils import split_lines


class LineAndTagV2(BaseModel):
    line: str
    stringified_line: str
    temporal_tags: set[Temporal]
    event_mention_tags: set[EventMention]
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

    temporal_tags, event_mention_tags, sentence_uuid = \
        qualify_line_interface.get_temporal_and_event_mention_tags(stringified_line)

    return LineAndTagV2(
        line=line,
        stringified_line=stringified_line,
        temporal_tags=temporal_tags,
        event_mention_tags=event_mention_tags,
        sentence_uuid=sentence_uuid,
    )
