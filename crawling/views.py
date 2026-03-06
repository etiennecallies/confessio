from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from crawling.models import CrawlingModeration
from front.views import get_moderate_response
from registry.models.base_moderation_models import BUG_DESCRIPTION_MAX_LENGTH


@login_required
@permission_required("scheduling.change_sentence")
def moderate_crawling(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'crawling', is_bug, diocese_slug,
                                 CrawlingModeration, moderation_uuid, render_crawling_moderation)


def render_crawling_moderation(request, moderation: CrawlingModeration, next_url):
    return render(request, f'moderations/moderate_crawling.html', {
        'website': moderation.website,
        'moderation': moderation,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })
