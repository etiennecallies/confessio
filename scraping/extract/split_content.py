from uuid import UUID

from pydantic import BaseModel

from scraping.extract.tag_line import Tag, get_tags_with_regex
from scraping.prune.action_interfaces import BaseActionInterface
from scraping.prune.models import Action, Source
from scraping.refine.refine_content import remove_link_from_html


class LineAndTag(BaseModel):
    line: str
    line_without_link: str
    tags: set[Tag]
    action: Action
    source: Source | None
    sentence_uuid: UUID | None


def split_lines(refined_content: str) -> list[str]:
    return refined_content.split('<br>\n')


def split_and_tag(refined_content: str, action_interface: BaseActionInterface
                  ) -> list[LineAndTag]:
    results = []

    # Split into lines (or <table>)
    for line in split_lines(refined_content):
        line_without_link = remove_link_from_html(line)

        tags = get_tags_with_regex(line_without_link)
        action, source, sentence_uuid = action_interface.get_action(line_without_link)
        results.append(LineAndTag(
            line=line,
            line_without_link=line_without_link,
            tags=tags,
            action=action,
            source=source,
            sentence_uuid=sentence_uuid,
        ))

    return results
