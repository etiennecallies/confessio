from fetching.models import OClocherOrganization, OClocherMatchingModeration, OClocherMatching
from fetching.models.oclocher_moderation_models import OClocherOrganizationModeration
from registry.models import Website


def add_organization_moderation(website: Website,
                                category: OClocherOrganizationModeration.Category,
                                oclocher_organization: OClocherOrganization | None = None,
                                ):
    try:
        moderation = OClocherOrganizationModeration.objects.get(website=website, category=category)
        if moderation.oclocher_organization != oclocher_organization:
            moderation.oclocher_organization = oclocher_organization
            moderation.save()
    except OClocherOrganizationModeration.DoesNotExist:
        moderation = OClocherOrganizationModeration(
            website=website, category=category,
            diocese=website.get_diocese(),
            oclocher_organization=oclocher_organization,
        )
        moderation.save()


def add_matching_moderation(oclocher_organization: OClocherOrganization,
                            oclocher_matching: OClocherMatching,
                            category: OClocherMatchingModeration.Category,
                            ):
    try:
        OClocherMatchingModeration.objects.get(
            oclocher_matching=oclocher_matching,
            category=category
        )
    except OClocherMatchingModeration.DoesNotExist:
        moderation = OClocherMatchingModeration(
            oclocher_matching=oclocher_matching,
            diocese=oclocher_organization.website.get_diocese(),
            category=category,
        )
        moderation.save()
