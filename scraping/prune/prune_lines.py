from dataclasses import dataclass
from typing import Optional, Tuple, Set

from scraping.extract.tag_line import Tag
from scraping.prune.models import Action, Source

MAX_PRE_BUFFERING_ATTEMPTS = 3
MAX_POST_BUFFERING_ATTEMPTS = 3


@dataclass
class PreBuffer:
    last_period_line: Optional[int] = None
    last_date_line: Optional[int] = None
    remaining_attempts: int = MAX_PRE_BUFFERING_ATTEMPTS

    def to_buffer(self) -> list[int]:
        return sorted(filter(
            lambda x: x is not None,
            [self.last_period_line, self.last_date_line]
        ))

    def from_tags(self, tags: set[Tag], i: int):
        if Tag.PERIOD in tags:
            self.last_period_line = i
        if Tag.DATE in tags:
            self.last_date_line = i
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

    def add_line(self, i: int, tags: Set[Tag], paragraph_indices: list[int]):
        self.buffer.append(i)
        self.is_post_schedule = self.is_post_schedule or Tag.SCHEDULE in tags
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


def get_pruned_lines_indices(lines_and_tags: list[Tuple[str, str, set[Tag], Action, Source]]
                             ) -> list[list[int]]:
    results = []
    paragraph_indices = []
    pre_buffer: Optional[PreBuffer] = None
    post_buffer: Optional[PostBuffer] = None

    for i, (line, line_without_link, tags, action, source) in enumerate(lines_and_tags):
        # print(line, tags)
        if Tag.CONFESSION in tags and action == Action.SHOW:
            if post_buffer is None:
                post_buffer = PostBuffer(
                    buffer=[] if pre_buffer is None else pre_buffer.to_buffer()
                )
                pre_buffer = None
            post_buffer.add_line(i, tags, paragraph_indices)
        elif action == Action.STOP:
            pre_buffer = None
            if post_buffer is not None:
                post_buffer = None
                paragraph_indices = flush_results(paragraph_indices, results)
        elif (Tag.DATE in tags or Tag.PERIOD in tags or source is not None) \
                and action == Action.SHOW:
            if post_buffer is None:
                if pre_buffer is None:
                    pre_buffer = PreBuffer()
                pre_buffer.from_tags(tags, i)
            else:
                post_buffer.add_line(i, tags, paragraph_indices)
        elif Tag.SCHEDULE in tags and action == Action.SHOW:
            if post_buffer is not None:
                post_buffer.add_line(i, tags, paragraph_indices)
            elif pre_buffer is not None:
                pre_buffer = pre_buffer.decrement()
        elif pre_buffer is not None:
            pre_buffer = pre_buffer.decrement()
        elif post_buffer is not None:
            post_buffer = post_buffer.decrement(i, action)
            if post_buffer is None:
                paragraph_indices = flush_results(paragraph_indices, results)

    flush_results(paragraph_indices, results)

    return results
