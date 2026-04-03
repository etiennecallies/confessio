from django.contrib.auth.decorators import login_required, permission_required

from core.views import get_moderate_response
from crawling.models import CrawlingModeration


@login_required
@permission_required("scheduling.change_sentence")
def moderate_crawling(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'crawling', is_bug, diocese_slug,
                                 CrawlingModeration, moderation_uuid,
                                 create_crawling_moderation_context)


def create_crawling_moderation_context(moderation: CrawlingModeration) -> dict:
    return {
        'website': moderation.website,
    }
