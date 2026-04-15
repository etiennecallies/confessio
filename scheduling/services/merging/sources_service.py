from fetching.public_service import fetching_get_oclocher_id_by_location_id
from registry.models import Church
from scheduling.public_model import BaseSource, ParsingSource, OClocherSource
from scheduling.services.merging.oclocher_schedules_services import \
    get_schedules_list_from_oclocher_schedules
from scheduling.services.merging.timezone_service import get_website_timezone
from scheduling.services.parsing.parsing_service import get_parsing_schedules_list
from scheduling.services.parsing.church_desc_service import get_church_by_id
from scheduling.services.scheduling.scheduling_service import SchedulingSources


def get_church_by_id_and_sources(scheduling_sources: SchedulingSources,
                                 ) -> tuple[dict[int, Church], list[BaseSource]]:
    church_by_id = get_church_by_id(scheduling_sources.churches)

    sources = []
    for parsing in scheduling_sources.parsings:
        sources.append(ParsingSource(
            schedules_list=get_parsing_schedules_list(parsing),
            parsing_uuid=parsing.uuid,
        ))

    if scheduling_sources.oclocher_schedules:
        oclocher_matching = scheduling_sources.oclocher_matching
        assert oclocher_matching is not None

        oclocher_id_by_location_id = fetching_get_oclocher_id_by_location_id(
            scheduling_sources.oclocher_locations)

        timezone_str = get_website_timezone(scheduling_sources.churches)

        schedules_list = get_schedules_list_from_oclocher_schedules(
            scheduling_sources.oclocher_schedules,
            oclocher_matching,
            oclocher_id_by_location_id,
            timezone_str,
        )
        sources.append(OClocherSource(schedules_list=schedules_list))

    return church_by_id, sources
