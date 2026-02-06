from background_task import background
from background_task.tasks import TaskSchedule

from attaching.models import Image
from attaching.services.upload_image_service import get_image_public_url
from scheduling.utils.hash_utils import hash_string_to_hex
from core.utils.log_utils import info
from scheduling.process import init_scheduling
from scheduling.workflows.parsing.llm_client import LLMProvider
from attaching.workflows.recognize.recognize_image_with_llm import (get_html_from_image, get_prompt,
                                                                    get_llm_model)
from crawling.workflows.scrape.download_refine_and_extract import get_extracted_html_list
from attaching.services.image_service import get_image_html
from scheduling.services.pruning.prune_scraping_service import create_pruning


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
    extracted_html_list = get_extracted_html_list(get_image_html(image))
    if not extracted_html_list:
        return

    prunings = []
    for extracted_html_item in extracted_html_list:
        prunings.append(create_pruning(extracted_html_item))

    image.prunings.clear()
    for pruning in prunings:
        image.prunings.add(pruning)
