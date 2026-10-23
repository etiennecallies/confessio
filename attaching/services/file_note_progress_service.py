from uuid import UUID

from attaching.models import FileNote
from core.services.background_task_service import TaskStatus, get_task_status_by_first_arg

# Matches the @background task in attaching/tasks.py (module path + function name).
RECOGNIZE_FILE_NOTE_TASK_NAME = 'attaching.tasks.worker_recognize_and_extract_file_note'


def get_file_note_recognition_status_by_website_uuid(website_uuids: set[str]
                                                     ) -> dict[str, TaskStatus]:
    """Map each website UUID owning a file note with a pending/running recognition task to its
    TaskStatus. The task is keyed by file note UUID, so we resolve those back to their website.
    """
    if not website_uuids:
        return {}

    status_by_file_note_uuid = get_task_status_by_first_arg(RECOGNIZE_FILE_NOTE_TASK_NAME)
    if not status_by_file_note_uuid:
        return {}

    file_note_uuids = []
    for arg in status_by_file_note_uuid:
        try:
            file_note_uuids.append(UUID(arg))
        except ValueError:  # not a file note uuid, the queue row is not ours to read
            continue

    status_by_website_uuid: dict[str, TaskStatus] = {}
    for file_note_uuid, website_uuid in FileNote.objects.filter(uuid__in=file_note_uuids,
                                                                website_id__in=website_uuids)\
            .values_list('uuid', 'website_id'):
        status = status_by_file_note_uuid[str(file_note_uuid)]
        # IN_PROGRESS wins if a website has several pending file notes
        if status_by_website_uuid.get(str(website_uuid)) != TaskStatus.IN_PROGRESS:
            status_by_website_uuid[str(website_uuid)] = status
    return status_by_website_uuid
