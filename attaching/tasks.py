from background_task import background
from background_task.tasks import TaskSchedule

from attaching.models import FileNote, TextNote
from attaching.services.worker_recognize_service import recognize_file_note, extract_file_note, \
    extract_text_note
from core.utils.log_utils import info
from scheduling.public_service import scheduling_init_scheduling


@background(queue='main', schedule=TaskSchedule(priority=3))
def worker_recognize_and_extract_file_note(file_note_uuid: str):
    try:
        file_note = FileNote.objects.get(uuid=file_note_uuid)
    except FileNote.DoesNotExist as e:
        info(f'FileNote {file_note_uuid} does not exist: {e}')
        return

    recognize_file_note(file_note)
    extract_file_note(file_note)
    scheduling_init_scheduling(file_note.website)


@background(queue='main', schedule=TaskSchedule(priority=3))
def worker_extract_text_note(text_note_uuid: str):
    try:
        text_note = TextNote.objects.get(uuid=text_note_uuid)
    except TextNote.DoesNotExist as e:
        info(f'TextNote {text_note_uuid} does not exist: {e}')
        return

    extract_text_note(text_note)
    scheduling_init_scheduling(text_note.website)
