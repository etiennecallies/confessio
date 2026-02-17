from pydantic import BaseModel

from scheduling.workflows.merging.sourced_schedules import SourcedSchedulesOfChurch
from scheduling.workflows.merging.sources import BaseSource


class SourcedSchedulesList(BaseModel):
    sourced_schedules_of_churches: list[SourcedSchedulesOfChurch]
    possible_by_appointment_sources: list[BaseSource]
    is_related_to_mass_sources: list[BaseSource]
    is_related_to_adoration_sources: list[BaseSource]
    is_related_to_permanence_sources: list[BaseSource]
    will_be_seasonal_events_sources: list[BaseSource]
