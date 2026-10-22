from attaching.models import FileNote


def get_file_note_html(file_note: FileNote) -> str | None:
    return file_note.human_html or file_note.llm_html
