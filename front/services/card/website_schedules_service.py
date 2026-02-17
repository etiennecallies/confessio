from dataclasses import dataclass
from uuid import UUID

from front.services.card.church_color_service import get_church_color_by_uuid
from front.services.card.sources_service import sort_parsings
from registry.models import Church, Website
from scheduling.models import Parsing
from scheduling.models import Scheduling
from scheduling.public_model import SourcedSchedulesList
from scheduling.services.merging.sourced_schedules_service import get_sourced_schedules_list
from scheduling.services.merging.sources_service import get_church_by_id_and_sources
from scheduling.services.scheduling.scheduling_service import get_scheduling_sources


@dataclass
class WebsiteSchedules:
    sourced_schedules_list: SourcedSchedulesList
    church_by_id: dict[int, Church]
    parsing_index_by_parsing_uuid: dict[UUID, int]
    parsing_by_uuid: dict[UUID, Parsing]
    church_color_by_uuid: dict[UUID, str]


def get_scheduling_elements(website: Website,
                            scheduling: Scheduling | None,
                            ) -> tuple[SourcedSchedulesList, dict[int, Church], list[Parsing]]:
    scheduling_sources = get_scheduling_sources(scheduling)
    church_by_id, sources = get_church_by_id_and_sources(scheduling_sources)

    sourced_schedules_list = get_sourced_schedules_list(website, church_by_id, sources)

    return sourced_schedules_list, church_by_id, scheduling_sources.parsings


def get_website_schedules(website: Website,
                          scheduling: Scheduling | None,
                          ) -> WebsiteSchedules:
    sourced_schedules_list, church_by_id, parsings = get_scheduling_elements(website, scheduling)

    parsing_index_by_parsing_uuid = {
        parsing.uuid: i for i, parsing in enumerate(sort_parsings(parsings))
    }
    parsing_by_uuid = {parsing.uuid: parsing for parsing in parsings}

    return WebsiteSchedules(
        sourced_schedules_list=sourced_schedules_list,
        church_by_id=church_by_id,
        parsing_index_by_parsing_uuid=parsing_index_by_parsing_uuid,
        parsing_by_uuid=parsing_by_uuid,
        church_color_by_uuid=get_church_color_by_uuid(sourced_schedules_list, church_by_id),
    )
