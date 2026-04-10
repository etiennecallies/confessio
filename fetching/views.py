import json

from django.contrib.auth.decorators import login_required, permission_required

from core.views import get_moderate_response
from fetching.models import OClocherOrganizationModeration, OClocherMatchingModeration


@login_required
@permission_required("scheduling.change_sentence")
def moderate_oclocher_organization(request, category, status, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'oclocher_organization', status, diocese_slug,
                                 OClocherOrganizationModeration,
                                 moderation_uuid,
                                 create_oclocher_organization_moderation_context)


def create_oclocher_organization_moderation_context(
        moderation: OClocherOrganizationModeration) -> dict:
    website = moderation.website
    assert website is not None

    return {
        'website': website,
    }


@login_required
@permission_required("scheduling.change_sentence")
def moderate_oclocher_matching(request, category, status, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'oclocher_matching', status, diocese_slug,
                                 OClocherMatchingModeration,
                                 moderation_uuid,
                                 create_oclocher_matching_moderation_context)


def create_oclocher_matching_moderation_context(
        moderation: OClocherMatchingModeration) -> dict:
    oclocher_matching = moderation.oclocher_matching
    assert oclocher_matching is not None
    church_desc_by_id_json = json.dumps(oclocher_matching.church_desc_by_id,
                                        indent=2, ensure_ascii=False)
    location_desc_by_id_json = json.dumps(oclocher_matching.location_desc_by_id,
                                          indent=2, ensure_ascii=False)
    locations_with_schedules = []
    if moderation.oclocher_organization:
        for location in moderation.oclocher_organization.locations.all():
            if location.schedules.exists():
                locations_with_schedules.append(location)

    return {
        'oclocher_matching': oclocher_matching,
        'church_desc_by_id_json': church_desc_by_id_json,
        'location_desc_by_id_json': location_desc_by_id_json,
        'locations_with_schedules': locations_with_schedules,
    }
