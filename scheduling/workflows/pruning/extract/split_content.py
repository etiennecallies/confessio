from uuid import UUID

from pydantic import BaseModel

from scheduling.utils.html_utils import split_lines, stringify_html
from scheduling.workflows.pruning.extract.action_interfaces import BaseActionInterface
from scheduling.workflows.pruning.extract.models import Action, Source
from scheduling.workflows.pruning.extract.tag_line import Tag, get_tags_with_regex


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
