from django.db import models

from home.models.base_models import TimeStampMixin


class ChurchIndexEvent(TimeStampMixin):
    church = models.ForeignKey('Church', on_delete=models.CASCADE, related_name='events')
    day = models.DateField(db_index=True, null=True)
    start_time = models.TimeField(db_index=True, null=True)
    indexed_end_time = models.TimeField(db_index=True, null=True)
    displayed_end_time = models.TimeField(db_index=False, null=True)
    is_explicitely_other = models.BooleanField(null=True)
