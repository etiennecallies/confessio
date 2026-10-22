from attaching.models import FileNote, FileNoteModeration


def get_new_file_note_moderation(file_note: FileNote) -> FileNoteModeration | None:
    return file_note.moderations.filter(category=FileNoteModeration.Category.NEW_FILE_NOTE)\
        .first()
