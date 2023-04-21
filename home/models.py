import uuid

from django.contrib.gis.db import models as gis_models
from django.db import models


# Create your models here.


class TimeStampMixin(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        get_latest_by = ['updated_at']


class Parish(TimeStampMixin):
    name = models.CharField(max_length=100)
    home_url = models.URLField()
    confession_hours_url = models.URLField(null=True, blank=True)
    _latest_scraping = None
    _has_search_latest_scraping = False

    def get_latest_scraping(self) -> 'Scraping':
        if not self._has_search_latest_scraping:
            try:
                self._latest_scraping = self.scrapings.latest()
            except Scraping.DoesNotExist:
                self._latest_scraping = None
            self._has_search_latest_scraping = False

        return self._latest_scraping


class Church(TimeStampMixin):
    name = models.CharField(max_length=100)
    location = gis_models.PointField()
    address = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=5)
    city = models.CharField(max_length=50)
    parish = models.ForeignKey('Parish', on_delete=models.CASCADE, related_name='churches')


class Scraping(TimeStampMixin):
    confession_html = models.TextField()
    nb_iterations = models.PositiveSmallIntegerField()
    parish = models.ForeignKey('Parish', on_delete=models.CASCADE, related_name='scrapings')
