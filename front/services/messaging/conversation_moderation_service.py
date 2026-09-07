from front.models import Conversation, ConversationModeration
from registry.models.base_moderation_models import ModerationStatus


def upsert_conversation_moderation(conversation: Conversation) -> ConversationModeration:
    """Flag a conversation as waiting for a human, on every message we receive.

    A conversation already validated whose correspondent writes again goes back to TO_VALIDATE:
    that is a new question, even if the previous one got its answer.
    """
    # get_or_create so that two mails received at the same time don't both insert
    moderation, created = ConversationModeration.objects.get_or_create(
        conversation=conversation,
        category=ConversationModeration.Category.NEW_MESSAGE,
        defaults={'status': ModerationStatus.TO_VALIDATE},
    )
    if not created and moderation.status != ModerationStatus.TO_VALIDATE:
        moderation.status = ModerationStatus.TO_VALIDATE
        moderation.save()

    return moderation
