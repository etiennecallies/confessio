from background_task import background
from background_task.tasks import TaskSchedule

from attaching.models import Image
from attaching.services.worker_recognize_service import recognize_image, extract_image
from core.utils.log_utils import info
from scheduling.services.scheduling.scheduling_process_service import init_scheduling


@background(queue='main', schedule=TaskSchedule(priority=3))
def worker_recognize_and_extract_image(image_uuid: str):
    try:
        image = Image.objects.get(uuid=image_uuid)
    except Image.DoesNotExist as e:
        info(f'Image {image_uuid} does not exist: {e}')
        return

    recognize_image(image)
    extract_image(image)
    init_scheduling(image.website)
