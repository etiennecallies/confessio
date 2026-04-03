from fetching.models import OClocherMatching, OClocherLocation
from fetching.services.oclocher_matching_service import get_matching_matrix, \
    match_churches_and_locations, get_oclocher_id_by_location_id
from fetching.services.oclocher_organization_website_service import \
    handle_website_widgets
from fetching.workflows.oclocher.oclocher_matrix import OClocherMatrix
from registry.models import Website, Church


def fetching_handle_website_widgets(website: Website, organization_ids: set[str]):
    return handle_website_widgets(website, organization_ids)


def fetching_get_matching_matrix(oclocher_matching: OClocherMatching) -> OClocherMatrix | None:
    return get_matching_matrix(oclocher_matching)


def fetching_match_churches_and_locations(churches: list[Church], locations: list[OClocherLocation]
                                          ) -> OClocherMatching:
    return match_churches_and_locations(churches, locations)


def fetching_get_oclocher_id_by_location_id(locations: list[OClocherLocation]) -> dict:
    return get_oclocher_id_by_location_id(locations)
