from core.utils.log_utils import info
from fetching.models import OClocherOrganization
from fetching.models.oclocher_moderation_models import OClocherOrganizationModeration
from fetching.services.oclocher_moderations_service import add_organization_moderation
from registry.models import Website


def match_organizations_by_hypertext(website: Website) -> list[OClocherOrganization]:
    return OClocherOrganization.objects.filter(hypertext_redirected=website.home_url).all()


def add_oclocher_organization_for_website(website: Website, organization_ids: set[str]):
    if len(organization_ids) > 1:
        info(f"Multiple oclocher organization IDs found for website {website}: "
             f"{organization_ids}. Not updating.")
        add_organization_moderation(website,
                                    OClocherOrganizationModeration.Category.MULTIPLE_WIDGETS)
        return

    organization_id = organization_ids.pop()
    organization_with_this_id = OClocherOrganization.objects\
        .filter(organization_id=organization_id).first()
    if organization_with_this_id is None:
        info(f"Oclocher organization not found with ID {organization_id} for website {website}."
             f" Not updating.")
        add_organization_moderation(website,
                                    OClocherOrganizationModeration.Category.NOT_FOUND)
        return

    if organization_with_this_id.website == website:
        info(f"Oclocher organization ID for website {website} "
             f"remains unchanged: {organization_id}")
        return

    if not organization_with_this_id.website:
        info(f"Setting oclocher organization ID {organization_id} for website {website}")
        organization_with_this_id.website = website
        organization_with_this_id.save()
        return

    info(f"Oclocher organization ID {organization_id} for website {website} "
         f"conflicts with website {organization_with_this_id.website}. Not updating.")
    add_organization_moderation(website,
                                OClocherOrganizationModeration.Category.SHARED_WIDGET,
                                oclocher_organization=organization_with_this_id)


def remove_oclocher_organization_for_website(website: Website):
    try:
        organization = OClocherOrganization.objects.get(website=website)
        info(f"Removing oclocher organization ID {organization.organization_id}"
             f" for website {website} due to no widgets found nor hypertext match.")
        organization.delete()
    except OClocherOrganization.DoesNotExist:
        pass


def handle_website_widgets(website: Website, widget_organization_ids: set[str]):
    if widget_organization_ids:
        add_oclocher_organization_for_website(website, widget_organization_ids)
        return

    matched_organizations = match_organizations_by_hypertext(website)
    matched_organization_ids = set([o.organization_id for o in matched_organizations])
    if matched_organization_ids:
        add_oclocher_organization_for_website(website, matched_organization_ids)
        return

    remove_oclocher_organization_for_website(website)
