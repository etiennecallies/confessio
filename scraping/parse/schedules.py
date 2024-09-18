from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ScheduleItem(BaseModel, frozen=True):
    church_id: Optional[int]
    rdates: str
    exdates: str
    rrules: str
    exrules: str
    duration_in_minutes: Optional[int]
    during_school_holidays: Optional[bool]


class SchedulesList(BaseModel):
    schedules: list[ScheduleItem]
    possible_by_appointment: bool
    is_related_to_mass: bool
    is_related_to_adoration: bool
    is_related_to_permanence: bool


class Event(BaseModel, frozen=True):
    church_id: Optional[int]
    start: datetime
    end: datetime
