import uuid
from typing import List, Optional

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
    name = models.CharField(max_length=300)
    home_url = models.URLField(unique=True)

    _pages = None
    _latest_crawling = None
    _has_search_latest_crawling = False

    def get_latest_crawling(self) -> Optional['Crawling']:
        if not self._has_search_latest_crawling:
            try:
                self._latest_crawling = self.crawlings.latest()
            except Crawling.DoesNotExist:
                self._latest_crawling = None
            self._has_search_latest_crawling = True

        return self._latest_crawling

    def has_been_crawled(self) -> bool:
        return self.get_latest_crawling() is not None

    def get_pages(self) -> List['Page']:
        if self._pages is None:
            self._pages = self.pages.filter(deleted_at__isnull=True)

        return self._pages

    def has_pages(self) -> bool:
        return len(self.get_pages()) > 0

    def all_pages_scraped(self) -> bool:
        return all(map(Page.has_been_scraped, self.get_pages()))

    def one_page_has_confessions(self) -> bool:
        return any(map(Page.has_confessions, self.get_pages()))


class ParishSource(TimeStampMixin):
    name = models.CharField(max_length=100)
    messesinfo_network_id = models.CharField(max_length=100, null=True)
    messesinfo_community_id = models.CharField(max_length=100, null=True, unique=True)
    parish = models.ForeignKey('Parish', on_delete=models.CASCADE, related_name='sources')


class Church(TimeStampMixin):
    name = models.CharField(max_length=100)
    location = gis_models.PointField(geography=True)
    address = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=5)
    city = models.CharField(max_length=50)
    messesinfo_id = models.CharField(max_length=100, null=True, unique=True)
    parish = models.ForeignKey('Parish', on_delete=models.CASCADE, related_name='churches')
    parish_source = models.ForeignKey('ParishSource', on_delete=models.SET_NULL,
                                      blank=True, null=True, related_name='churches')


class Page(TimeStampMixin):
    url = models.URLField()
    deleted_at = models.DateTimeField(null=True)
    parish = models.ForeignKey('Parish', on_delete=models.CASCADE, related_name='pages')

    _latest_scraping = None
    _has_search_latest_scraping = False

    def get_latest_scraping(self) -> Optional['Scraping']:
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
            and self.get_latest_scraping().confession_html


class Crawling(TimeStampMixin):
    error_detail = models.TextField(null=True)
    nb_visited_links = models.PositiveSmallIntegerField()
    nb_success_links = models.PositiveSmallIntegerField()
    parish = models.ForeignKey('Parish', on_delete=models.CASCADE, related_name='crawlings')


class Scraping(TimeStampMixin):
    confession_html = models.TextField(null=True)
    nb_iterations = models.PositiveSmallIntegerField()
    page = models.ForeignKey('Page', on_delete=models.CASCADE, related_name='scrapings')


class Sentence(TimeStampMixin):
    line = models.TextField(null=False, unique=True)
    is_confession = models.BooleanField()
    is_schedule = models.BooleanField()
    is_date = models.BooleanField()
    is_period = models.BooleanField()
    is_place = models.BooleanField()
    is_spiritual = models.BooleanField()
    is_other = models.BooleanField()
