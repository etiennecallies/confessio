from fetching.models import OClocherOrganization
from fetching.models.oclocher_moderation_models import OClocherOrganizationModeration
from fetching.services.oclocher_moderations_service import add_organization_moderation
from home.utils.log_utils import info
from registry.models import Website
from scraping.crawl.extract_widgets import OClocherWidget


def remove_oclocher_organization_for_website(website: Website):
    try:
        organization = OClocherOrganization.objects.get(website=website)
        info(f"Removing oclocher organization ID {organization.organization_id}"
             f" for website {website} due to no widgets found")
        organization.delete()
    except OClocherOrganization.DoesNotExist:
        pass


def add_oclocher_organization_for_website(website: Website, oclocher_widgets: list[OClocherWidget]):
    organization_ids = set([w.organization_id for w in oclocher_widgets])
    if len(organization_ids) > 1:
        info(f"Multiple oclocher organization IDs found for website {website}: "
             f"{organization_ids}. Not updating.")
        add_organization_moderation(website,
                                    OClocherOrganizationModeration.Category.MULTIPLE_WIDGETS)
        return

    organization_id = organization_ids.pop()
    organization_with_this_id = OClocherOrganization.objects\
        .filter(organization_id=organization_id).first()
    if organization_with_this_id is not None:
        if organization_with_this_id.website == website:
            info(f"Oclocher organization ID for website {website} "
                 f"remains unchanged: {organization_id}")
            return

        info(f"Oclocher organization ID {organization_id} for website {website} "
             f"conflicts with website {organization_with_this_id.website}. Not updating.")
        add_organization_moderation(website,
                                    OClocherOrganizationModeration.Category.MULTIPLE_WIDGETS,
                                    oclocher_organization=organization_with_this_id)
        return

    info(f"Creating oclocher organization ID {organization_id} "
         f"for website {website}")
    oclocher_organization = OClocherOrganization(
        organization_id=organization_id,
        website=website
    )
    oclocher_organization.save()
