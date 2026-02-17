from fetching.services.oclocher_matching_service import get_matching_church_desc_by_id, \
    get_location_desc_by_id, get_matching_location_desc_by_id, get_location_desc
from front.services.card.timezone_service import get_timezone_of_churches
from registry.models import Church
from scheduling.services.merging.oclocher_schedules_services import \
    get_schedules_list_from_oclocher_schedules
from scheduling.services.parsing.parsing_service import get_parsing_schedules_list, \
    get_parsing_church_desc_by_id
from scheduling.services.scheduling.scheduling_service import SchedulingSources
from scheduling.utils.list_utils import get_desc_by_id
from scheduling.workflows.merging.sources import ParsingSource, BaseSource, OClocherSource


def get_church_by_id_and_sources(scheduling_sources: SchedulingSources,
                                 ) -> tuple[dict[int, Church], list[BaseSource]]:
    church_by_desc = {church.get_desc(): church for church in scheduling_sources.churches}
    church_desc_by_id = get_desc_by_id(list(church_by_desc.keys()))
    church_by_id = {church_id: church_by_desc[desc]
                    for church_id, desc in church_desc_by_id.items()}

    sources = []
    for parsing in scheduling_sources.parsings:
        assert get_parsing_church_desc_by_id(parsing) == church_desc_by_id, \
            f'Parsing churches: {get_parsing_church_desc_by_id(parsing)}' \
            f'Scheduling churches: {church_desc_by_id}'
        sources.append(ParsingSource(
            schedules_list=get_parsing_schedules_list(parsing),
            parsing_uuid=parsing.uuid,
        ))

    if scheduling_sources.oclocher_schedules:
        oclocher_matching = scheduling_sources.oclocher_matching
        assert oclocher_matching is not None
        assert get_matching_church_desc_by_id(oclocher_matching) == church_desc_by_id

        location_desc_by_id = get_location_desc_by_id(scheduling_sources.oclocher_locations)
        assert get_matching_location_desc_by_id(oclocher_matching) == location_desc_by_id
        location_by_desc = {get_location_desc(location): location
                            for location in scheduling_sources.oclocher_locations}
        oclocher_id_by_location_id = {location_id: location_by_desc[desc].location_id
                                      for location_id, desc in location_desc_by_id.items()}

        timezone_str = get_timezone_of_churches(scheduling_sources.churches)

        schedules_list = get_schedules_list_from_oclocher_schedules(
            scheduling_sources.oclocher_schedules,
            oclocher_matching,
            oclocher_id_by_location_id,
            timezone_str,
        )
        sources.append(OClocherSource(schedules_list=schedules_list))

    return church_by_id, sources
