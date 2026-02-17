from dataclasses import dataclass
from uuid import UUID

from front.services.card.church_color_service import get_church_color_by_uuid
from front.services.card.sources_service import sort_parsings
from registry.models import Church
from scheduling.models import Scheduling
from scheduling.public_model import SourcedSchedulesList
from scheduling.public_service import scheduling_retrieve_scheduling_elements


@dataclass
class WebsiteSchedules:
    sourced_schedules_list: SourcedSchedulesList
    church_by_id: dict[int, Church]
    parsing_index_by_parsing_uuid: dict[UUID, int]
    church_color_by_uuid: dict[UUID, str]


def get_website_schedules(scheduling: Scheduling | None,
                          ) -> WebsiteSchedules:
    scheduling_elements = scheduling_retrieve_scheduling_elements(scheduling)

    parsing_index_by_parsing_uuid = {
        parsing.uuid: i for i, parsing in enumerate(sort_parsings(scheduling_elements.parsings))
    }

    church_color_by_uuid = get_church_color_by_uuid(scheduling_elements.sourced_schedules_list,
                                                    scheduling_elements.church_by_id)

    return WebsiteSchedules(
        sourced_schedules_list=scheduling_elements.sourced_schedules_list,
        church_by_id=scheduling_elements.church_by_id,
        parsing_index_by_parsing_uuid=parsing_index_by_parsing_uuid,
        church_color_by_uuid=church_color_by_uuid,
    )
