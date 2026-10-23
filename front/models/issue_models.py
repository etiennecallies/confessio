from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

from core.models.base_models import BaseComment, BaseUserReport
from registry.models import ModerationMixin
from registry.models.base_moderation_models import ModerationStatus


class Issue(BaseUserReport):
    website = models.ForeignKey('registry.Website', on_delete=models.CASCADE,
                                related_name='issues')
    church = models.ForeignKey('registry.Church', on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='issues')
    content = models.TextField()
    solved_at = models.DateTimeField(null=True, blank=True)

    history = HistoricalRecords()


class IssueComment(BaseComment):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')


class IssueModeration(ModerationMixin):
    class Category(models.TextChoices):
        NEW_ISSUE = "new_issue"
        NEW_COMMENT = "new_comment"

    resource = 'issue'
    diocese = models.ForeignKey('registry.Diocese', on_delete=models.CASCADE,
                                related_name=f'{resource}_moderations')
    history = HistoricalRecords()
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='moderations')
    category = models.CharField(max_length=16, choices=Category)

    class Meta:
        unique_together = ('issue', 'category')

    def delete_on_validate(self) -> bool:
        # we keep the row, to keep track of which issues have been reviewed
        return False

    def validate(self, user: User | None):
        super().validate(user)
        if self.issue.solved_at is None:
            self.issue.solved_at = timezone.now()
            self.issue.save()

    def set_status(self, new_status: ModerationStatus, user: User):
        super().set_status(new_status, user)
        if new_status != ModerationStatus.VALIDATED and self.issue.solved_at is not None:
            self.issue.solved_at = None
            self.issue.save()
