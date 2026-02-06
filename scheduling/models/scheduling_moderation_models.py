from django.db import models
from simple_history.models import HistoricalRecords

from registry.models import ModerationMixin


class SchedulingModeration(ModerationMixin):
    class Category(models.TextChoices):
        NO_SOURCE = "no_source"
        NO_SCHEDULE = "no_schedule"
        UNKNOWN_PLACE = "unknown_place"
        SCHEDULES_CONFLICT = "sched_conflict"
        OK = "ok"

    resource = 'scheduling'
    validated_by = models.ForeignKey('auth.User', related_name=f'{resource}_validated_by',
                                     on_delete=models.SET_NULL, null=True)
    marked_as_bug_by = models.ForeignKey('auth.User', related_name=f'{resource}_marked_as_bug_by',
                                         on_delete=models.SET_NULL, null=True)
    diocese = models.ForeignKey('registry.Diocese', on_delete=models.CASCADE,
                                related_name=f'{resource}_moderations', null=True)
    history = HistoricalRecords()
    website = models.OneToOneField('registry.Website', on_delete=models.CASCADE,
                                   related_name=f'{resource}_moderation')
    category = models.CharField(max_length=16, choices=Category)

    def delete_on_validate(self) -> bool:
        return False
