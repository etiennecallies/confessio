from django.db import models

from core.models.base_models import TimeStampMixin


class Log(TimeStampMixin):
    class Type(models.TextChoices):
        PRUNING = "pruning"
        PARSING = "parsing"

    class Status(models.TextChoices):
        DONE = "done"
        FAILURE = "failure"

    website = models.ForeignKey('home.Website', on_delete=models.CASCADE,
                                related_name='scheduling_logs')
    content = models.TextField()
    type = models.CharField(max_length=8, choices=Type)
    status = models.CharField(max_length=8, choices=Status)
