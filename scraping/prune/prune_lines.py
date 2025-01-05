from dataclasses import dataclass
from typing import Optional

from scraping.extract.split_content import LineAndTag
from scraping.extract.tag_line import Tag
from scraping.prune.models import Action

MAX_PRE_BUFFERING_ATTEMPTS = 3
MAX_POST_BUFFERING_ATTEMPTS = 3


class IndexLine(LineAndTag):
    index: int

    def __lt__(self, other: 'IndexLine'):
        return self.index < other.index


@dataclass
class PreBuffer:
    last_period_line: Optional[IndexLine] = None
    last_date_line: Optional[IndexLine] = None
    remaining_attempts: int = MAX_PRE_BUFFERING_ATTEMPTS

    def to_buffer(self) -> list[IndexLine]:
        buffer = [il for il in [self.last_period_line, self.last_date_line] if il is not None]
        return sorted(buffer)

    def from_tags(self, index_line: IndexLine):
        if Tag.PERIOD in index_line.tags:
            self.last_period_line = index_line
        if Tag.DATE in index_line.tags:
            self.last_date_line = index_line
        self.remaining_attempts = MAX_PRE_BUFFERING_ATTEMPTS

    def decrement(self) -> 'Optional[PreBuffer]':
        if self.remaining_attempts == 0:
            return None

        self.remaining_attempts -= 1

        return self


@dataclass
class PostBuffer:
    buffer: list[int]
    is_post_schedule: bool = False
    remaining_attempts: int = MAX_POST_BUFFERING_ATTEMPTS

    @classmethod
    def from_pre_buffer(cls, pre_buffer: PreBuffer | None, paragraph_indices: list[int]
                        ) -> 'PostBuffer':
        post_buffer = cls(buffer=[])
        if pre_buffer is not None:
            for index_line in pre_buffer.to_buffer():
                post_buffer.add_line(index_line, paragraph_indices)

        return post_buffer

    def add_line(self, index_line: IndexLine, paragraph_indices: list[int]):
        self.buffer.append(index_line.index)
        self.is_post_schedule = self.is_post_schedule or Tag.SCHEDULE in index_line.tags
        self.remaining_attempts = MAX_POST_BUFFERING_ATTEMPTS
        if self.is_post_schedule:
            paragraph_indices.extend(self.buffer)
            self.buffer = []

    def decrement(self, i: int, action: Action) -> 'Optional[PostBuffer]':
        if self.remaining_attempts == 0:
            return None

        if action != Action.HIDE:
            self.remaining_attempts -= 1
            self.buffer.append(i)

        return self


def flush_results(paragraph_indices: list[int], results: list[list[int]]) -> list[int]:
    if paragraph_indices:
        results.append(paragraph_indices)
    return []


def get_pruned_lines_indices(lines_and_tags: list[LineAndTag]) -> list[list[int]]:
    results = []
    paragraph_indices = []
    pre_buffer: Optional[PreBuffer] = None
    post_buffer: Optional[PostBuffer] = None

    for i, line_and_tag in enumerate(lines_and_tags):
        index_line = IndexLine(index=i, **line_and_tag.model_dump())

        tags = line_and_tag.tags
        action = line_and_tag.action
        source = line_and_tag.source

        # print(line, tags)
        if Tag.CONFESSION in tags \
                and action in (Action.START, Action.SHOW):
            if post_buffer is None:
                post_buffer = PostBuffer.from_pre_buffer(pre_buffer, paragraph_indices)
                pre_buffer = None
            post_buffer.add_line(index_line, paragraph_indices)
        elif action == Action.STOP:
            pre_buffer = None
            if post_buffer is not None:
                post_buffer = None
                paragraph_indices = flush_results(paragraph_indices, results)
        elif (Tag.DATE in tags or Tag.PERIOD in tags or source is not None) \
                and action in (Action.START, Action.SHOW):
            if post_buffer is not None:
                post_buffer.add_line(index_line, paragraph_indices)
            elif action == Action.START:
                if pre_buffer is None:
                    pre_buffer = PreBuffer()
                pre_buffer.from_tags(index_line)
        elif Tag.SCHEDULE in tags and post_buffer is not None \
                and action in (Action.START, Action.SHOW):
            post_buffer.add_line(index_line, paragraph_indices)
        elif pre_buffer is not None and Tag.SCHEDULE not in tags:
            pre_buffer = pre_buffer.decrement()
        elif post_buffer is not None:
            post_buffer = post_buffer.decrement(i, action)
            if post_buffer is None:
                paragraph_indices = flush_results(paragraph_indices, results)

    flush_results(paragraph_indices, results)

    return results
