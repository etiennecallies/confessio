from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from core.views import get_moderate_response
from front.models import ConversationModeration, Message, ReportModeration
from front.services.moderation_stats_service import get_moderation_stats_by_diocese


@login_required
@permission_required("scheduling.change_sentence")
def moderation_home(request):
    return render(request, 'pages/moderation_home.html', {
        'dioceses_with_stats': get_moderation_stats_by_diocese(),
    })


@login_required
@permission_required("scheduling.change_sentence")
def moderate_report(request, category, status, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'report', status, diocese_slug,
                                 ReportModeration, moderation_uuid,
                                 create_report_moderation_context)


def create_report_moderation_context(moderation: ReportModeration) -> dict:
    report = moderation.report
    assert report is not None

    return {
        'report': report,
    }


@login_required
@permission_required("scheduling.change_sentence")
def moderate_conversation(request, category, status, diocese_slug, moderation_uuid=None):
    return get_moderate_response(request, category, 'conversation', status, diocese_slug,
                                 ConversationModeration, moderation_uuid,
                                 create_conversation_moderation_context)


def create_conversation_moderation_context(moderation: ConversationModeration) -> dict:
    conversation = moderation.conversation
    # Message.Meta orders by created_at, so last() is the latest one received.
    last_message = conversation.messages.filter(direction=Message.Direction.INBOUND).last()

    return {
        'conversation': conversation,
        'last_message': last_message,
    }
