from django.db import models

from core.models.base_models import TimeStampMixin


class IndexEvent(TimeStampMixin):
    scheduling = models.ForeignKey('scheduling.Scheduling', on_delete=models.CASCADE,
                                   related_name='index_events')
    church = models.ForeignKey('registry.Church', on_delete=models.CASCADE,
                               related_name='index_events')
    day = models.DateField(db_index=True)
    start_time = models.TimeField(db_index=True)
    indexed_end_time = models.TimeField(db_index=True)
    displayed_end_time = models.TimeField(db_index=False, null=True)
    is_explicitely_other = models.BooleanField(null=True)
    has_been_moderated = models.BooleanField()
    church_color = models.CharField(max_length=9)

    class Meta:
        unique_together = ('church', 'day', 'start_time', 'displayed_end_time',
                           'is_explicitely_other')
