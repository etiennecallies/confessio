from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from core.views import get_moderate_response
from front.models import ReportModeration
from registry.models.base_moderation_models import BUG_DESCRIPTION_MAX_LENGTH


@login_required
@permission_required("scheduling.change_sentence")
def moderate_report(request, category, is_bug, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'report', is_bug, diocese_slug,
                                 ReportModeration, moderation_uuid, render_report_moderation)


def render_report_moderation(request, moderation: ReportModeration, next_url):
    report = moderation.report
    assert report is not None

    return render(request, f'moderations/moderate_report.html', {
        'report': report,
        'moderation': moderation,
        'next_url': next_url,
        'bug_description_max_length': BUG_DESCRIPTION_MAX_LENGTH,
    })
