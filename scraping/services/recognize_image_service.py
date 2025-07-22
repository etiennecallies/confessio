from home.models import Image, Website
from home.services.upload_image_service import get_image_public_url
from home.utils.hash_utils import hash_string_to_hex
from scraping.parse.llm_client import LLMProvider
from scraping.recognize.recognize_image_with_llm import (get_html_from_image, get_prompt,
                                                         get_llm_model)
from scraping.scrape.download_refine_and_extract import get_extracted_html_list
from scraping.services.image_service import get_image_html
from scraping.services.prune_scraping_service import create_pruning, prune_pruning


def recognize_images_for_website(website: Website):
    for image in website.images.all():
        recognize_and_parse_image(image)


def recognize_and_parse_image(image: Image):
    if image.llm_provider is not None:
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

    extract_and_prune_image(image)


def extract_and_prune_image(image: Image):
    # Extract
    extracted_html_list = get_extracted_html_list(get_image_html(image))
    if not extracted_html_list:
        return

    # Prune
    prunings = []
    for extracted_html_item in extracted_html_list:
        prunings.append(create_pruning(extracted_html_item))

    image.prunings.clear()
    for pruning in prunings:
        image.prunings.add(pruning)

    for pruning in prunings:
        prune_pruning(pruning)
