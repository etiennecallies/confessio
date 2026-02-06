from background_task import background
from background_task.tasks import TaskSchedule

from attaching.models import Image
from attaching.services.image_service import get_image_html
from attaching.services.upload_image_service import get_image_public_url
from attaching.workflows.recognize.recognize_image_with_llm import (get_html_from_image, get_prompt,
                                                                    get_llm_model)
from core.utils.llm_utils import LLMProvider
from core.utils.log_utils import info
from crawling.public_worflow import crawling_get_extracted_html_list
from scheduling.services.scheduling.scheduling_process_service import init_scheduling
from scheduling.public_service import scheduling_create_pruning
from scheduling.utils.hash_utils import hash_string_to_hex


def recognize_and_extract_image(image: Image):
    worker_recognize_and_extract_image(str(image.uuid))


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


def recognize_image(image: Image):
    if image.llm_provider is not None:
        print(f'Image {image.uuid} already recognized with LLM')
        return

    print(f'Recognizing image {image.uuid} with LLM')

    prompt = get_prompt()
    prompt_hash = hash_string_to_hex(prompt)
    llm_provider = LLMProvider.OPENAI
    llm_model = get_llm_model()
    llm_html, llm_error_details = get_html_from_image(get_image_public_url(image),
                                                      prompt, llm_provider, llm_model)

    if llm_error_details:
        image.llm_error_details = llm_error_details
    else:
        image.llm_html = llm_html
    image.prompt_hash = prompt_hash
    image.llm_provider = llm_provider
    image.llm_model = llm_model
    image.save()


def extract_image(image: Image):
    extracted_html_list = crawling_get_extracted_html_list(get_image_html(image))
    if not extracted_html_list:
        return

    prunings = []
    for extracted_html_item in extracted_html_list:
        prunings.append(scheduling_create_pruning(extracted_html_item))

    image.prunings.clear()
    for pruning in prunings:
        image.prunings.add(pruning)
