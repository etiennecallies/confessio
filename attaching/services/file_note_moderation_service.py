from attaching.models import FileNote, FileNoteModeration
from registry.models.base_moderation_models import ModerationStatus


def add_necessary_moderation_for_file_note(file_note: FileNote):
    """Flag an anonymously uploaded file note, so that a human looks at it."""
    file_note_moderation = FileNoteModeration(
        file_note=file_note,
        category=FileNoteModeration.Category.NEW_FILE_NOTE,
        diocese=file_note.website.get_diocese(),
        status=ModerationStatus.TO_VALIDATE,
    )
    file_note_moderation.save()


def get_new_file_note_moderation(file_note: FileNote) -> FileNoteModeration | None:
    return file_note.moderations.filter(category=FileNoteModeration.Category.NEW_FILE_NOTE)\
        .first()
