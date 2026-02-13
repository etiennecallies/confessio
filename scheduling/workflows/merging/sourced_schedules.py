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


class SourcedSchedulesList(BaseModel):
    sourced_schedules_of_churches: list[SourcedSchedulesOfChurch]
    possible_by_appointment_sources: list[BaseSource]
    is_related_to_mass_sources: list[BaseSource]
    is_related_to_adoration_sources: list[BaseSource]
    is_related_to_permanence_sources: list[BaseSource]
    will_be_seasonal_events_sources: list[BaseSource]
