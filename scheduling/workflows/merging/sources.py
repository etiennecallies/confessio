from abc import ABC, abstractmethod
from uuid import UUID

from pydantic import BaseModel

from scheduling.workflows.parsing.schedules import SchedulesList


class BaseSource(BaseModel, ABC, frozen=True):
    schedules_list: SchedulesList | None

    @property
    @abstractmethod
    def source_type(self) -> str:
        pass

    @abstractmethod
    def __hash__(self):
        pass


class ParsingSource(BaseSource):
    parsing_uuid: UUID

    @property
    def source_type(self) -> str:
        return 'parsing'

    def __hash__(self):
        return hash((self.source_type, self.parsing_uuid))


class OClocherSource(BaseSource):

    @property
    def source_type(self) -> str:
        return 'oclocher'

    def __hash__(self):
        return hash(self.source_type)


UnionSource = ParsingSource | OClocherSource
