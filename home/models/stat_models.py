from home.models.base_models import TimeStampMixin
from django.db import models


class Log(TimeStampMixin):
    class Type(models.TextChoices):
        CRAWLING = "crawling"
        SCRAPING = "scraping"
        PRUNING = "pruning"
        PARSING = "parsing"

    class Status(models.TextChoices):
        DONE = "done"
        TIMEOUT = "timeout"
        FAILURE = "failure"

    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='logs')
    content = models.TextField()
    type = models.CharField(max_length=8, choices=Type)
    status = models.CharField(max_length=8, choices=Status, null=True)  # TODO set as not null
