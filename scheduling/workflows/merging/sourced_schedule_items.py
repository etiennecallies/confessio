from pydantic import BaseModel

from scheduling.workflows.merging.sources import BaseSource
from scraping.parse.schedules import ScheduleItem, Event


class SourcedScheduleItem(BaseModel):
    item: ScheduleItem
    explanation: str
    sources: list[BaseSource]
    events: list[Event]
