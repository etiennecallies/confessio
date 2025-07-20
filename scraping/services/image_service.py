from home.models import Image


def get_image_html(image: Image) -> str | None:
    return image.human_html or image.llm_html
