from home.models import ModerationMixin
from django.db import models
from simple_history.models import HistoricalRecords


class ParsingModeration(ModerationMixin):
    class Category(models.TextChoices):
        NEW_SCHEDULES = "new_schedules"
        SCHEDULES_DIFFER = "schedules_differ"
        LLM_ERROR = "llm_error"

    resource = 'parsing'
    validated_by = models.ForeignKey('auth.User', related_name=f'{resource}_validated_by',
                                     on_delete=models.SET_NULL, null=True)
    marked_as_bug_by = models.ForeignKey('auth.User', related_name=f'{resource}_marked_as_bug_by',
                                         on_delete=models.SET_NULL, null=True)
    diocese = models.ForeignKey('home.Diocese', on_delete=models.CASCADE,
                                related_name=f'{resource}_moderations', null=True)
    history = HistoricalRecords()
    parsing = models.ForeignKey('home.Parsing', on_delete=models.CASCADE,
                                related_name='moderations')
    category = models.CharField(max_length=16, choices=Category)

    class Meta:
        unique_together = ('parsing', 'category')

    def delete_on_validate(self) -> bool:
        # we always keep validated ParsingModeration
        return False
