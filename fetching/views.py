import json

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from fetching.models import OClocherOrganizationModeration, OClocherMatchingModeration
from front.views import get_moderate_response
from registry.models.base_moderation_models import BUG_DESCRIPTION_MAX_LENGTH


@login_required
@permission_required("scheduling.change_sentence")
def moderate_oclocher_organization(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'oclocher_organization', is_bug, diocese_slug,
                                 OClocherOrganizationModeration,
                                 moderation_uuid, render_oclocher_organization_moderation)


def render_oclocher_organization_moderation(request, moderation: OClocherOrganizationModeration,
                                            next_url):
    website = moderation.website
    assert website is not None

    return render(request, f'moderations/moderate_oclocher_organization.html', {
        'website': website,
        'moderation': moderation,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


@login_required
@permission_required("scheduling.change_sentence")
def moderate_oclocher_matching(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'oclocher_matching', is_bug, diocese_slug,
                                 OClocherMatchingModeration,
                                 moderation_uuid, render_oclocher_matching_moderation)


def render_oclocher_matching_moderation(request, moderation: OClocherMatchingModeration,
                                        next_url):
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

    return render(request, f'moderations/moderate_oclocher_matching.html', {
        'oclocher_matching': oclocher_matching,
        'moderation': moderation,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
        'church_desc_by_id_json': church_desc_by_id_json,
        'location_desc_by_id_json': location_desc_by_id_json,
        'locations_with_schedules': locations_with_schedules,
    })
