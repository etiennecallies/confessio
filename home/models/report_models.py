from django.db import models

from home.models.base_models import TimeStampMixin


class Report(TimeStampMixin):
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='reports')

    class FeedbackType(models.TextChoices):
        GOOD = "good"
        OUTDATED = "outdated"
        ERROR = "error"
        COMMENT = "comment"

    class ErrorType(models.TextChoices):
        CHURCHES = "churches"
        PARAGRAPHS = "paragraphs"
        SCHEDULES = "schedules"

    feedback_type = models.CharField(max_length=8, choices=FeedbackType.choices)
    error_type = models.CharField(max_length=10, choices=ErrorType.choices, null=True)

    comment = models.TextField(null=True)
    user_agent = models.TextField(null=True)
    ip_address_hash = models.CharField(max_length=64, null=True)
