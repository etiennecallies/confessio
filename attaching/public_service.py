from attaching.models import FileNote, FileNoteModeration, Image, ImageModeration
from attaching.services.file_note_moderation_service import get_new_file_note_moderation
from attaching.services.image_moderation_service import get_new_image_moderation
from attaching.services.image_progress_service import \
    get_image_recognition_status_by_website_uuid
from attaching.services.upload_image_service import upload_image, get_image_public_url, \
    find_error_in_document_to_upload, get_file_note_public_url
from attaching.services.worker_recognize_service import recognize_pdf
from attaching.tasks import worker_recognize_and_extract_image
from core.services.background_task_service import TaskStatus
from registry.models import Website


def attaching_upload_image(document, website: Website, request, comment: str | None = None,
                           ) -> tuple[Image | None, str | None]:
    return upload_image(document, website, request, comment=comment)


def attaching_find_error_in_document_to_upload(document) -> str | None:
    return find_error_in_document_to_upload(document)


def attaching_recognize_and_extract_image(image: Image):
    worker_recognize_and_extract_image(str(image.uuid))


def attaching_get_image_public_url(image: Image) -> str:
    return get_image_public_url(image)


def attaching_get_new_image_moderation(image: Image) -> ImageModeration | None:
    return get_new_image_moderation(image)


def attaching_get_file_note_public_url(file_note: FileNote) -> str:
    return get_file_note_public_url(file_note)


def attaching_get_new_file_note_moderation(file_note: FileNote) -> FileNoteModeration | None:
    return get_new_file_note_moderation(file_note)


def attaching_recognize_pdf(pdf_url: str, pdf_bytes: bytes) -> str | None:
    return recognize_pdf(pdf_url, pdf_bytes)


def attaching_get_image_recognition_status_by_website_uuid(
        website_uuids: set[str]) -> dict[str, TaskStatus]:
    return get_image_recognition_status_by_website_uuid(website_uuids)
