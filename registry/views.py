from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from front.views import get_moderate_response
from registry.models import WebsiteModeration, ChurchModeration, ParishModeration
from registry.models.base_moderation_models import BUG_DESCRIPTION_MAX_LENGTH


@login_required
@permission_required("scheduling.change_sentence")
def moderate_website(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'website', is_bug, diocese_slug,
                                 WebsiteModeration, moderation_uuid, render_website_moderation)


def render_website_moderation(request, moderation: WebsiteModeration, next_url):
    return render(request, f'moderations/moderate_website.html', {
        'website_moderation': moderation,
        'website': moderation.website,
        'latest_crawling': moderation.website.crawling,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


@login_required
@permission_required("scheduling.change_sentence")
def moderate_parish(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'parish', is_bug, diocese_slug,
                                 ParishModeration, moderation_uuid, render_parish_moderation)


def render_parish_moderation(request, moderation: ParishModeration, next_url):
    return render(request, f'moderations/moderate_parish.html', {
        'parish_moderation': moderation,
        'parish': moderation.parish,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })


@login_required
@permission_required("scheduling.change_sentence")
def moderate_church(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'church', is_bug, diocese_slug,
                                 ChurchModeration, moderation_uuid, render_church_moderation)


def render_church_moderation(request, moderation: ChurchModeration, next_url):
    return render(request, f'moderations/moderate_church.html', {
        'church_moderation': moderation,
        'church': moderation.church,
        'similar_churches': moderation.get_similar_churches_sorted_by_name(),
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })
