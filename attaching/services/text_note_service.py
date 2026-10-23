from django.utils.html import linebreaks

from attaching.models import TextNote


def get_text_note_html(text_note: TextNote) -> str:
    return linebreaks(text_note.content, autoescape=True)
