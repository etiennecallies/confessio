from attaching.models import Image, ImageModeration
from registry.models.base_moderation_models import ModerationStatus


def add_necessary_moderation_for_image(image: Image):
    """Flag an anonymously uploaded image, so that a human looks at it."""
    image_moderation = ImageModeration(
        image=image,
        category=ImageModeration.Category.NEW_IMAGE,
        diocese=image.website.get_diocese(),
        status=ModerationStatus.TO_VALIDATE,
    )
    image_moderation.save()


def get_new_image_moderation(image: Image) -> ImageModeration | None:
    return image.moderations.filter(category=ImageModeration.Category.NEW_IMAGE).first()
