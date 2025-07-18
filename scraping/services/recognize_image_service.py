from home.models import Image
from home.services.image_service import get_image_public_url
from home.utils.hash_utils import hash_string_to_hex
from scraping.parse.llm_client import LLMProvider
from scraping.recognize.recognize_image_with_llm import (get_html_from_image, get_prompt,
                                                         get_llm_model)


def recognize_image(image: Image):
    if image.llm_html is not None:
        return

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
