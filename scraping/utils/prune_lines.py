from dataclasses import dataclass
from typing import Optional, List, Tuple, Set

from scraping.utils.tag_line import Tag

MAX_BUFFERING_ATTEMPTS = 2


@dataclass
class PreBuffer:
    last_period_line: Optional[int] = None
    last_date_line: Optional[int] = None
    last_place_line: Optional[int] = None
    remaining_attempts: int = MAX_BUFFERING_ATTEMPTS

    def to_buffer(self) -> List[int]:
        return sorted(filter(
            lambda x: x is not None,
            [self.last_place_line, self.last_date_line, self.last_place_line]
        ))

    def from_tags(self, tags: Set[Tag], i: int):
        if Tag.PERIOD in tags:
            self.last_period_line = i
        if Tag.DATE in tags:
            self.last_date_line = i
        if Tag.PLACE in tags:
            self.last_place_line = i

    def decrement(self) -> 'Optional[PreBuffer]':
        if self.remaining_attempts == 0:
            return None

        self.remaining_attempts -= 1

        return self


@dataclass
class PostBuffer:
    buffer: List[int]
    is_post_schedule: bool = False
    remaining_attempts: int = MAX_BUFFERING_ATTEMPTS

    def add_line(self, i: int, tags: Set[Tag], results: List[int]):
        self.buffer.append(i)
        self.is_post_schedule = self.is_post_schedule or Tag.SCHEDULE in tags
        self.remaining_attempts = MAX_BUFFERING_ATTEMPTS
        if self.is_post_schedule:
            results.extend(self.buffer)
            self.buffer = []

    def decrement(self, i: int, tags: Set[Tag]) -> 'Optional[PostBuffer]':
        if self.remaining_attempts == 0:
            return None

        if Tag.SPIRITUAL not in tags:
            self.remaining_attempts -= 1
            self.buffer.append(i)

        return self


def get_pruned_lines_indices(lines_and_tags: List[Tuple[str, str, Set[Tag]]]) -> List[int]:
    results = []
    pre_buffer: Optional[PreBuffer] = None
    post_buffer: Optional[PostBuffer] = None

    for i, (line, line_without_link, tags) in enumerate(lines_and_tags):
        # print(line, tags)
        if Tag.CONFESSION in tags:
            if post_buffer is None:
                post_buffer = PostBuffer(
                    buffer=[] if pre_buffer is None else pre_buffer.to_buffer()
                )
                pre_buffer = None
            post_buffer.add_line(i, tags, results)
        elif Tag.OTHER in tags:
            if not (Tag.SCHEDULE in tags or
                    Tag.SPIRITUAL in tags or
                    Tag.DATE in tags or
                    Tag.PERIOD in tags or
                    Tag.PLACE in tags):
                pre_buffer = None
                post_buffer = None
        elif Tag.SCHEDULE in tags:
            if post_buffer is not None:
                post_buffer.add_line(i, tags, results)
            elif pre_buffer is not None:
                pre_buffer.decrement()
        elif Tag.DATE in tags or Tag.PERIOD in tags or Tag.PLACE in tags:
            if post_buffer is None:
                if pre_buffer is None:
                    pre_buffer = PreBuffer()
                pre_buffer.from_tags(tags, i)
            else:
                post_buffer.add_line(i, tags, results)
        elif pre_buffer is not None:
            pre_buffer = pre_buffer.decrement()
        elif post_buffer is not None:
            post_buffer = post_buffer.decrement(i, tags)

    return results
