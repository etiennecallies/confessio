from django.db import models
from simple_history.models import HistoricalRecords

from core.models.base_models import TimeStampMixin
from registry.models import ModerationMixin


class Conversation(TimeStampMixin):
    """An email thread with one external correspondent.

    Its uuid is the thread key: it travels in every outgoing body as a /messaging/<uuid> link,
    and is read back from the quoted text of inbound replies.
    """
    email = models.EmailField()
    name = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.subject} — {self.email}'


class Message(TimeStampMixin):
    class Direction(models.TextChoices):
        OUTBOUND = "outbound"  # admin -> correspondent
        INBOUND = "inbound"  # correspondent -> admin

    class Status(models.TextChoices):
        RECEIVED = "received"
        SENT = "sent"
        FAILED = "failed"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,
                                     related_name='messages')
    direction = models.CharField(max_length=10, choices=Direction.choices)
    body = models.TextField()
    # Outbound: the admin who wrote it. Inbound: null.
    author = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='sent_messages')
    # Inbound: the raw From header. It differs from conversation.email on contact-form mails,
    # which we send from no-reply@ with the visitor in Reply-To.
    from_email = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices)
    error_message = models.TextField(blank=True)
    # The RFC 5322 Message-ID this mail was delivered under, quoted by the next one in
    # In-Reply-To/References so mail clients keep the thread together. Outbound: SES's, which
    # overwrites the one Django sets. Inbound: the header Mailgun forwards. Empty if unknown.
    message_id = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.conversation_id} {self.direction} {self.created_at}'


class ConversationModeration(ModerationMixin):
    class Category(models.TextChoices):
        NEW_MESSAGE = "new_message"

    resource = 'conversation'
    # A conversation hangs off no diocese: these moderations land in the "Autre" bucket.
    diocese = models.ForeignKey('registry.Diocese', on_delete=models.CASCADE,
                                related_name=f'{resource}_moderations', null=True)
    history = HistoricalRecords()
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,
                                     related_name='moderations')
    category = models.CharField(max_length=16, choices=Category)

    class Meta:
        unique_together = ('conversation', 'category')

    def delete_on_validate(self) -> bool:
        # We keep the row: the next inbound message puts it back to TO_VALIDATE.
        return False
