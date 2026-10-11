import mimetypes
from datetime import timedelta

from attaching.models import FileNote, FileNoteModeration, Image, ImageModeration

FILE_NOTE_DEFAULT_TTL = timedelta(days=365)


def mirror_image(image: Image):
    # Same uuid as the image, so that moderations find their parent and backfill is idempotent
    FileNote.objects.update_or_create(uuid=image.uuid, defaults=get_file_note_fields(image))


def get_file_note_fields(image: Image) -> dict:
    return {
        'website_id': image.website_id,
        'user_id': image.user_id,
        'user_agent': image.user_agent,
        'ip_address_hash': image.ip_address_hash,
        'name': image.name,
        'caption': image.comment,
        'mime_type': mimetypes.guess_type(image.name)[0] or 'application/octet-stream',
        'llm_html': image.llm_html,
        'llm_provider': image.llm_provider,
        'llm_model': image.llm_model,
        'llm_prompt_hash': image.prompt_hash,
        'llm_error_detail': image.llm_error_detail,
        'human_html': image.human_html,
        'expire_at': image.created_at + FILE_NOTE_DEFAULT_TTL,
    }


def delete_image_mirror(image: Image):
    FileNote.objects.filter(uuid=image.uuid).delete()


def mirror_image_prunings(image: Image):
    file_note = FileNote.objects.filter(uuid=image.uuid).first()
    if file_note is not None:
        file_note.prunings.set(image.prunings.all())


def mirror_image_moderation(moderation: ImageModeration):
    # Image may predate the double write: the backfill command will handle it
    if not FileNote.objects.filter(uuid=moderation.image_id).exists():
        return

    FileNoteModeration.objects.update_or_create(
        uuid=moderation.uuid, defaults=get_file_note_moderation_fields(moderation))


def get_file_note_moderation_fields(moderation: ImageModeration) -> dict:
    return {
        'file_note_id': moderation.image_id,
        'category': FileNoteModeration.Category.NEW_FILE_NOTE,
        'diocese_id': moderation.diocese_id,
        'status': moderation.status,
        'comment': moderation.comment,
    }


def delete_image_moderation_mirror(moderation: ImageModeration):
    FileNoteModeration.objects.filter(uuid=moderation.uuid).delete()
