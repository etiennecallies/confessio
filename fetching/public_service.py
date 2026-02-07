from fetching.services.oclocher_organization_service import add_oclocher_organization_for_website, \
    remove_oclocher_organization_for_website
from registry.models import Website


def fetching_add_oclocher_organization_for_website(website: Website, organization_ids: set[str]):
    return add_oclocher_organization_for_website(website, organization_ids)


def fetching_remove_oclocher_organization_for_website(website: Website):
    return remove_oclocher_organization_for_website(website)
