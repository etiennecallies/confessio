from django.db import models
from simple_history.models import HistoricalRecords

from core.models.base_models import TimeStampMixin
from registry.models import ModerationMixin


class Crawling(TimeStampMixin):
    error_detail = models.TextField(null=True)
    nb_visited_links = models.PositiveSmallIntegerField()
    nb_success_links = models.PositiveSmallIntegerField()
    recrawl_triggered_at = models.DateTimeField(null=True, blank=True)


class Scraping(TimeStampMixin):
    url = models.URLField(max_length=300)
    website = models.ForeignKey('registry.Website', on_delete=models.CASCADE,
                                related_name='scrapings')
    prunings = models.ManyToManyField('scheduling.Pruning', related_name='scrapings')

    history = HistoricalRecords()

    class Meta:
        unique_together = ('url', 'website')


class WebsiteForbiddenPath(TimeStampMixin):
    website = models.ForeignKey('registry.Website', on_delete=models.CASCADE,
                                related_name='forbidden_paths')
    path = models.CharField(max_length=300)

    class Meta:
        unique_together = ('website', 'path')


class Log(TimeStampMixin):
    class Type(models.TextChoices):
        CRAWLING = "crawling"
        SCRAPING = "scraping"

    class Status(models.TextChoices):
        DONE = "done"
        TIMEOUT = "timeout"
        FAILURE = "failure"

    started_at = models.DateTimeField(null=True)  # TODO make not null
    end_at = models.DateTimeField(null=True)  # TODO make not null
    website = models.ForeignKey('registry.Website', on_delete=models.CASCADE,
                                related_name='crawling_logs')
    content = models.TextField()
    type = models.CharField(max_length=8, choices=Type)
    status = models.CharField(max_length=8, choices=Status)


class CrawlingModeration(ModerationMixin):
    class Category(models.TextChoices):
        NO_RESPONSE = "no_resp"
        NO_PAGE = "no_page"
        OK = "ok"

    resource = 'crawling'
    validated_by = models.ForeignKey('auth.User', related_name=f'{resource}_validated_by',
                                     on_delete=models.SET_NULL, null=True)
    marked_as_bug_by = models.ForeignKey('auth.User', related_name=f'{resource}_marked_as_bug_by',
                                         on_delete=models.SET_NULL, null=True)
    diocese = models.ForeignKey('registry.Diocese', on_delete=models.CASCADE,
                                related_name=f'{resource}_moderations', null=True)
    history = HistoricalRecords()
    website = models.OneToOneField('registry.Website', on_delete=models.CASCADE,
                                   related_name=f'{resource}_moderation')
    category = models.CharField(max_length=8, choices=Category)

    def delete_on_validate(self) -> bool:
        return False
