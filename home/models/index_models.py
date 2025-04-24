from django.db import models

from home.models.base_models import TimeStampMixin


class WebsiteIndexEvent(TimeStampMixin):
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='events')
    church = models.ForeignKey('Church', on_delete=models.SET_NULL, related_name='events',
                               null=True)
    start = models.DateTimeField(db_index=True)
    end = models.DateTimeField(db_index=False, null=True)
    is_explicitely_other = models.BooleanField()
