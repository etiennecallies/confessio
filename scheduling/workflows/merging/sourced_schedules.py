from pydantic import BaseModel

from scheduling.workflows.merging.sources import BaseSource
from scheduling.workflows.parsing.schedules import ScheduleItem, Event


class SourcedScheduleItem(BaseModel):
    item: ScheduleItem
    explanation: str
    sources: list[BaseSource]
    events: list[Event]


class SourcedSchedulesOfChurch(BaseModel):
    church_id: int | None
    sourced_schedules: list[SourcedScheduleItem]

    def is_church_explicitly_other(self) -> bool:
        return self.church_id == -1
