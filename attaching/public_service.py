from attaching.models import Image
from attaching.services.upload_image_service import upload_image
from attaching.tasks import worker_recognize_and_extract_image
from registry.models import Website


def attaching_upload_image(document, website: Website, request
                           ) -> tuple[Image | None, str | None]:
    return upload_image(document, website, request)


def attaching_recognize_and_extract_image(image: Image):
    worker_recognize_and_extract_image(str(image.uuid))
