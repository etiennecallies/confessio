from attaching.models import Image
from attaching.tasks import worker_recognize_and_extract_image


def recognize_and_extract_image(image: Image):
    worker_recognize_and_extract_image(str(image.uuid))
