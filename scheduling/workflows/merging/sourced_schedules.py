from pydantic import BaseModel

from scheduling.workflows.merging.sources import UnionSource
from scheduling.workflows.parsing.schedules import ScheduleItem


class SourcedScheduleItem(BaseModel):
    item: ScheduleItem
    explanation: str
    sources: list[UnionSource]

    def hash_key(self):
        return self.explanation, tuple(sorted(map(lambda s: s.hash_key(), self.sources)))


class SourcedSchedulesOfChurch(BaseModel):
    church_id: int | None
    sourced_schedules: list[SourcedScheduleItem]

    def is_church_explicitly_other(self) -> bool:
        return self.church_id == -1

    def is_real_church(self) -> bool:
        return self.church_id is not None and not self.is_church_explicitly_other()

    def hash_key(self):
        return (
            self.church_id if self.church_id is not None else -2,
            tuple(sorted(map(lambda s: s.hash_key(), self.sourced_schedules)))
        )
