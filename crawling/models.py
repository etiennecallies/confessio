from django.db import models
from simple_history.models import HistoricalRecords

from core.models.base_models import TimeStampMixin


class Crawling(TimeStampMixin):
    error_detail = models.TextField(null=True)
    nb_visited_links = models.PositiveSmallIntegerField()
    nb_success_links = models.PositiveSmallIntegerField()
    recrawl_triggered_at = models.DateTimeField(null=True, blank=True)


class Scraping(TimeStampMixin):
    url = models.URLField(max_length=300)
    nb_iterations = models.PositiveSmallIntegerField()
    website = models.ForeignKey('home.Website', on_delete=models.CASCADE, related_name='scrapings')
    prunings = models.ManyToManyField('scheduling.Pruning', related_name='scrapings')

    history = HistoricalRecords()

    class Meta:
        unique_together = ('url', 'website')

    def has_confessions(self) -> bool:
        return any(pruning.has_confessions() for pruning in self.prunings.all())


class WebsiteForbiddenPath(TimeStampMixin):
    website = models.ForeignKey('home.Website', on_delete=models.CASCADE,
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

    website = models.ForeignKey('home.Website', on_delete=models.CASCADE,
                                related_name='crawling_logs')
    content = models.TextField()
    type = models.CharField(max_length=8, choices=Type)
    status = models.CharField(max_length=8, choices=Status)
