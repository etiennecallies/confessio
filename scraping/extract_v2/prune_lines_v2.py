from dataclasses import dataclass
from typing import Optional

from scraping.extract_v2.split_content import LineAndTagV2
from scraping.extract_v2.tag_line import EventMotion, TagV2

MAX_PRE_BUFFERING_ATTEMPTS = 3
MAX_POST_BUFFERING_ATTEMPTS = 3


class IndexLine(LineAndTagV2):
    index: int

    def __lt__(self, other: 'IndexLine'):
        return self.index < other.index


@dataclass
class PreBuffer:
    buffer: list[IndexLine] = None
    remaining_attempts: int = MAX_PRE_BUFFERING_ATTEMPTS

    def to_buffer(self) -> list[IndexLine]:
        return self.buffer

    def from_index_line(self, index_line: IndexLine):
        assert TagV2.SPECIFIER in index_line.tags
        if self.buffer is None:
            self.buffer = []
        self.buffer.append(index_line)
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
        self.is_post_schedule = self.is_post_schedule or TagV2.SCHEDULE in index_line.tags
        self.remaining_attempts = MAX_POST_BUFFERING_ATTEMPTS
        if self.is_post_schedule:
            paragraph_indices.extend(self.buffer)
            self.buffer = []

    def decrement(self, i: int, index_line: IndexLine,
                  ) -> 'Optional[PostBuffer]':
        if self.remaining_attempts == 0:
            return None

        if not index_line.tags and index_line.event_motion != EventMotion.START:
            self.remaining_attempts -= 1
            self.buffer.append(i)

        return self


def flush_results(paragraph_indices: list[int], results: list[list[int]]) -> list[int]:
    if paragraph_indices:
        results.append(paragraph_indices)
    return []


def get_pruned_lines_indices(lines_and_tags: list[LineAndTagV2]) -> list[list[int]]:
    results = []
    paragraph_indices = []
    pre_buffer: Optional[PreBuffer] = None
    post_buffer: Optional[PostBuffer] = None

    for i, line_and_tag in enumerate(lines_and_tags):
        index_line = IndexLine(index=i, **line_and_tag.model_dump())

        tags = line_and_tag.tags
        event_motion = line_and_tag.event_motion

        # print(line, tags, event_motion)

        # If we encounter a START, then we start a post_buffer
        if event_motion == EventMotion.START:
            if post_buffer is None:
                post_buffer = PostBuffer.from_pre_buffer(pre_buffer, paragraph_indices)
                pre_buffer = None
            post_buffer.add_line(index_line, paragraph_indices)

        # If we encounter a STOP, we flush the post_buffer if it exists
        elif event_motion == EventMotion.STOP and post_buffer is not None:
            post_buffer = None
            paragraph_indices = flush_results(paragraph_indices, results)

        # If we encounter a START or SHOW we add the line to the post_buffer
        elif post_buffer is not None \
                and event_motion in (EventMotion.START, EventMotion.SHOW):
            post_buffer.add_line(index_line, paragraph_indices)

        # If we encounter a SPECIFIER, we complete or create the pre_buffer
        elif TagV2.SPECIFIER in tags:
            if pre_buffer is None:
                pre_buffer = PreBuffer()
            pre_buffer.from_index_line(index_line)

        # If we have another line in pre_buffer context, we decrement it
        elif pre_buffer is not None \
                and TagV2.SCHEDULE not in tags \
                and TagV2.SPECIFIER not in tags \
                and event_motion != EventMotion.START:
            pre_buffer = pre_buffer.decrement()
        elif post_buffer is not None:
            post_buffer = post_buffer.decrement(i, index_line)
            if post_buffer is None:
                paragraph_indices = flush_results(paragraph_indices, results)

    flush_results(paragraph_indices, results)

    return results
