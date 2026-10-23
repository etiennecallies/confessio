from attaching.models import TextNote, TextNoteModeration
from registry.models.base_moderation_models import ModerationStatus


def add_necessary_moderation_for_text_note(text_note: TextNote):
    """Flag an anonymously added text note, so that a human looks at it."""
    text_note_moderation = TextNoteModeration(
        text_note=text_note,
        category=TextNoteModeration.Category.NEW_TEXT_NOTE,
        diocese=text_note.website.get_diocese(),
        status=ModerationStatus.TO_VALIDATE,
    )
    text_note_moderation.save()


def get_new_text_note_moderation(text_note: TextNote) -> TextNoteModeration | None:
    return text_note.moderations.filter(category=TextNoteModeration.Category.NEW_TEXT_NOTE)\
        .first()
