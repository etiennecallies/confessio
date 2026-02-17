from pydantic import BaseModel

from scheduling.workflows.merging.sourced_schedules import SourcedSchedulesOfChurch
from scheduling.workflows.merging.sources import UnionSource


class SourcedSchedulesList(BaseModel):
    sourced_schedules_of_churches: list[SourcedSchedulesOfChurch]
    possible_by_appointment_sources: list[UnionSource]
    is_related_to_mass_sources: list[UnionSource]
    is_related_to_adoration_sources: list[UnionSource]
    is_related_to_permanence_sources: list[UnionSource]
    will_be_seasonal_events_sources: list[UnionSource]
