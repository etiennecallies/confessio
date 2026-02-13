from django.db.models.functions import Now

from crawling.public_worflow import crawling_get_new_url_and_aliases
from crawling.workflows.crawl.download_and_search_urls import is_new_url_valid
from fetching.models import OClocherOrganization
from fetching.workflows.oclocher.fetch_oclocher_api import fetch_organizations


def fetch_oclocher_organizations() -> tuple[int, int, int, int, int]:
    organizations_as_dict = fetch_organizations()
    fetched = len(organizations_as_dict)

    existing_organizations = OClocherOrganization.objects.all()
    existing_organization_by_id = {
        orga.organization_id: orga for orga in existing_organizations
    }
    added = 0
    same = 0
    edited = 0
    for organization_as_dict in organizations_as_dict:
        organization_id = organization_as_dict['id']
        hypertext = organization_as_dict.get('hypertext')

        if organization_id in existing_organization_by_id:
            oclocher_organization = existing_organization_by_id[organization_id]
            del existing_organization_by_id[organization_id]
            if oclocher_organization.hypertext == hypertext:
                same += 1
                continue

            oclocher_organization.hypertext = hypertext
            oclocher_organization.save()
            redirect_hypertext(oclocher_organization)
            edited += 1
            continue

        oclocher_organization = OClocherOrganization(
            organization_id=organization_id,
            hypertext=hypertext,
        )
        oclocher_organization.save()
        redirect_hypertext(oclocher_organization)
        added += 1

    # Delete organizations that are no longer present
    deleted = 0
    for organization in existing_organization_by_id.values():
        organization.delete()
        deleted += 1

    return fetched, added, same, edited, deleted


def set_redirect_hypertext(oclocher_organization: OClocherOrganization,
                           hypertext_redirected: str | None):
    oclocher_organization.hypertext_redirected = hypertext_redirected
    oclocher_organization.redirected_at = Now()
    oclocher_organization.save()


def redirect_hypertext(oclocher_organization: OClocherOrganization):
    if not oclocher_organization.hypertext:
        set_redirect_hypertext(oclocher_organization, None)
        return

    new_home_url, aliases_domains, error_message = \
        crawling_get_new_url_and_aliases(oclocher_organization.hypertext)
    if not is_new_url_valid(new_home_url):
        print(f'This url is not eligible to hypertext redirect: {new_home_url}')
        set_redirect_hypertext(oclocher_organization, None)
        return

    if len(new_home_url) > 200:
        print(f'This url is too long to be hypertext redirect: {new_home_url}')
        set_redirect_hypertext(oclocher_organization, None)
        return

    set_redirect_hypertext(oclocher_organization, new_home_url)
