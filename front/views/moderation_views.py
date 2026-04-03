from django.contrib.auth.decorators import login_required, permission_required

from core.views import get_moderate_response
from front.models import ReportModeration


@login_required
@permission_required("scheduling.change_sentence")
def moderate_report(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'report', is_bug, diocese_slug,
                                 ReportModeration, moderation_uuid,
                                 create_report_moderation_context)


def create_report_moderation_context(moderation: ReportModeration) -> dict:
    report = moderation.report
    assert report is not None

    return {
        'report': report,
    }
