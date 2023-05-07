import uuid
from typing import List

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
    _pages = None

    def get_pages(self) -> List['Page']:
        if self._pages is None:
            self._pages = self.pages.all()

        return self._pages

    def has_pages(self) -> bool:
        return len(self.get_pages()) > 0

    def not_scraped_yet(self) -> bool:
        return not any(map(Page.has_been_scraped, self.get_pages()))

    def has_confessions(self) -> bool:
        return any(map(Page.has_confessions, self.get_pages()))


class Church(TimeStampMixin):
    name = models.CharField(max_length=100)
    location = gis_models.PointField()
    address = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=5)
    city = models.CharField(max_length=50)
    parish = models.ForeignKey('Parish', on_delete=models.CASCADE, related_name='churches')


class Page(TimeStampMixin):
    url = models.URLField()
    parish = models.ForeignKey('Parish', on_delete=models.CASCADE, related_name='pages')
    _latest_scraping = None
    _has_search_latest_scraping = False

    def get_latest_scraping(self) -> 'Scraping':
        if not self._has_search_latest_scraping:
            try:
                self._latest_scraping = self.scrapings.latest()
            except Scraping.DoesNotExist:
                self._latest_scraping = None
            self._has_search_latest_scraping = True

        return self._latest_scraping

    def has_been_scraped(self) -> bool:
        return self.get_latest_scraping() is not None

    def has_confessions(self) -> bool:
        return self.get_latest_scraping() is not None\
            and self.get_latest_scraping().confession_html is not None


class Scraping(TimeStampMixin):
    confession_html = models.TextField()
    nb_iterations = models.PositiveSmallIntegerField()
    page = models.ForeignKey('Page', on_delete=models.CASCADE, related_name='scrapings')
