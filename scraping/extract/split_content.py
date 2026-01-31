from uuid import UUID

from pydantic import BaseModel

from crawling.workflows.refine.refine_content import stringify_html
from scraping.extract.tag_line import Tag, get_tags_with_regex
from scheduling.workflows.pruning.action_interfaces import BaseActionInterface
from scheduling.workflows.pruning.models import Action, Source
from scraping.utils.html_utils import split_lines


class LineAndTag(BaseModel):
    line: str
    stringified_line: str
    tags: set[Tag]
    action: Action
    source: Source | None
    sentence_uuid: UUID | None


def split_and_tag(refined_content: str, action_interface: BaseActionInterface
                  ) -> list[LineAndTag]:
    results = []

    # Split into lines (or <table>)
    for line in split_lines(refined_content):
        stringified_line = stringify_html(line)

        tags = get_tags_with_regex(stringified_line)
        action, source, sentence_uuid = action_interface.get_action(stringified_line)
        results.append(LineAndTag(
            line=line,
            stringified_line=stringified_line,
            tags=tags,
            action=action,
            source=source,
            sentence_uuid=sentence_uuid,
        ))

    return results
