from django.contrib.auth.decorators import login_required, permission_required

from attaching.models import ImageModeration
from attaching.services.image_service import get_image_html
from core.views import get_moderate_response


@login_required
@permission_required("scheduling.change_sentence")
def moderate_image(request, category, status, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'image', status, diocese_slug,
                                 ImageModeration, moderation_uuid,
                                 create_image_moderation_context)


def create_image_moderation_context(moderation: ImageModeration) -> dict:
    image = moderation.image

    return {
        'image': image,
        'image_html': get_image_html(image),
    }
