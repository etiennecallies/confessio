from attaching.models import TextNote, TextNoteModeration


def get_new_text_note_moderation(text_note: TextNote) -> TextNoteModeration | None:
    return text_note.moderations.filter(category=TextNoteModeration.Category.NEW_TEXT_NOTE)\
        .first()
