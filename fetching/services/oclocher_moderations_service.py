from django.db.models.functions import Now

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


def upsert_matching_moderation(oclocher_organization: OClocherOrganization,
                               oclocher_matching: OClocherMatching,
                               category: OClocherMatchingModeration.Category,
                               moderation_validated: bool):
    try:
        moderation = OClocherMatchingModeration.objects.get(oclocher_matching=oclocher_matching)
        if moderation.category != category:
            moderation.category = category
            moderation.validated_at = Now() if moderation_validated else None
            moderation.validated_by = None
            moderation.save()
    except OClocherMatchingModeration.DoesNotExist:
        moderation = OClocherMatchingModeration(
            oclocher_matching=oclocher_matching, category=category,
            oclocher_organization=oclocher_organization,
            diocese=oclocher_organization.website.get_diocese(),
            validated_at=Now() if moderation_validated else None,
        )
        moderation.save()
