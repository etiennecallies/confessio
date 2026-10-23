from django.contrib.auth.decorators import login_required, permission_required

from attaching.models import FileNoteModeration, TextNoteModeration
from attaching.services.file_note_service import get_file_note_html
from attaching.services.text_note_service import get_text_note_html
from core.views import get_moderate_response


@login_required
@permission_required("scheduling.change_sentence")
def moderate_file_note(request, category, status, moderation_uuid=None):
    return get_moderate_response(request, category, 'file_note', status,
                                 FileNoteModeration, moderation_uuid,
                                 create_file_note_moderation_context)


def create_file_note_moderation_context(moderation: FileNoteModeration) -> dict:
    file_note = moderation.file_note

    return {
        'file_note': file_note,
        'file_note_html': get_file_note_html(file_note),
    }


@login_required
@permission_required("scheduling.change_sentence")
def moderate_text_note(request, category, status, moderation_uuid=None):
    return get_moderate_response(request, category, 'text_note', status,
                                 TextNoteModeration, moderation_uuid,
                                 create_text_note_moderation_context)


def create_text_note_moderation_context(moderation: TextNoteModeration) -> dict:
    text_note = moderation.text_note

    return {
        'text_note': text_note,
        'text_note_html': get_text_note_html(text_note),
    }
