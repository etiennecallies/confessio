from fetching.models import OClocherMatching, OClocherLocation
from fetching.services.oclocher_matching_service import get_matching_matrix, \
    match_churches_and_locations
from fetching.services.oclocher_organization_service import add_oclocher_organization_for_website, \
    remove_oclocher_organization_for_website
from fetching.workflows.oclocher.oclocher_matrix import OClocherMatrix
from registry.models import Website, Church


def fetching_add_oclocher_organization_for_website(website: Website, organization_ids: set[str]):
    return add_oclocher_organization_for_website(website, organization_ids)


def fetching_remove_oclocher_organization_for_website(website: Website):
    return remove_oclocher_organization_for_website(website)


def fetching_get_matching_matrix(oclocher_matching: OClocherMatching) -> OClocherMatrix | None:
    return get_matching_matrix(oclocher_matching)


def fetching_match_churches_and_locations(churches: list[Church], locations: list[OClocherLocation]
                                          ) -> OClocherMatching:
    return match_churches_and_locations(churches, locations)
