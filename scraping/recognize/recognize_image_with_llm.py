import openai
import os

from openai import BadRequestError

from scraping.parse.llm_client import LLMProvider


def get_prompt() -> str:
    return """Convert this image to HTML. Just output a valid HTML. Do not include any additional
    text or explanations.
    If there is no text in the image, just return an empty HTML document with <html></html> tags."""


def get_llm_model() -> str:
    return "gpt-4.1"  # or "gpt-4o-mini" if you prefer a smaller model


def remove_triple_quotes(text: str) -> str:
    """Remove triple quotes from the text."""
    return text.replace('```html', '').replace("```", '')


def get_html_from_image(image_url: str, prompt: str, llm_provider: LLMProvider,
                        llm_model: str) -> tuple[str | None, str | None]:
    assert llm_provider == LLMProvider.OPENAI
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY_RECOGNIZE"))

    try:
        response = openai_client.responses.create(
            model=llm_model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": image_url},
                    ],
                }
            ],
            temperature=0.0,
        )

        return remove_triple_quotes(response.output_text), None
    except BadRequestError as e:
        print(f"Error processing image {image_url}: {e}")
        return None, str(e)
