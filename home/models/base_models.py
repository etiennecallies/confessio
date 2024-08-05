import uuid
from typing import List, Optional

from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.db import models
from pgvector.django import VectorField
from simple_history.models import HistoricalRecords

from home.utils.hash_utils import hash_string_to_hex


class TimeStampMixin(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        get_latest_by = ['updated_at']


class Diocese(TimeStampMixin):
    name = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True)
    messesinfo_network_id = models.CharField(max_length=100, unique=True)
    history = HistoricalRecords()


class Website(TimeStampMixin):
    name = models.CharField(max_length=300)
    home_url = models.URLField(unique=True)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()

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
            self._pages = self.pages.all()

        return self._pages

    def has_pages(self) -> bool:
        return len(self.get_pages()) > 0

    def all_pages_scraped(self) -> bool:
        return all(map(Page.has_been_scraped, self.get_pages()))

    def all_pages_pruned(self) -> bool:
        return all(map(Page.latest_scraping_has_been_pruned, self.get_pages()))

    def one_page_has_confessions(self) -> bool:
        return any(map(Page.has_confessions, self.get_pages()))

    def delete_if_no_parish(self):
        if not self.parishes.exists():
            self.delete()


class Parish(TimeStampMixin):
    name = models.CharField(max_length=100)
    messesinfo_network_id = models.CharField(max_length=100, null=True)
    messesinfo_community_id = models.CharField(max_length=100, null=True, unique=True)
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='parishes',
                                null=True, blank=True)
    diocese = models.ForeignKey('Diocese', on_delete=models.CASCADE, related_name='parishes')
    history = HistoricalRecords()


class Church(TimeStampMixin):
    name = models.CharField(max_length=100)
    location = gis_models.PointField(geography=True, null=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    zipcode = models.CharField(max_length=5, null=True)
    city = models.CharField(max_length=50, null=True)
    messesinfo_id = models.CharField(max_length=100, null=True, unique=True, blank=True)
    parish = models.ForeignKey('Parish', on_delete=models.CASCADE,
                               related_name='churches')
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()


class Page(TimeStampMixin):
    url = models.URLField(unique=False)
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='pages')

    _latest_scraping = None
    _has_search_latest_scraping = False

    def get_latest_scraping(self) -> Optional['Scraping']:
        if not self._has_search_latest_scraping:
            try:
                self._latest_scraping = self.scraping
            except Scraping.DoesNotExist:
                self._latest_scraping = None
            self._has_search_latest_scraping = True

        return self._latest_scraping

    def has_been_scraped(self) -> bool:
        return self.get_latest_scraping() is not None

    def latest_scraping_has_been_pruned(self) -> bool:
        return self.get_latest_scraping() is not None\
            and self.get_latest_scraping().has_been_pruned()

    def has_confessions(self) -> bool:
        return self.get_latest_scraping() is not None\
            and self.get_latest_scraping().pruning is not None\
            and self.get_latest_scraping().pruning.pruned_html is not None


class Crawling(TimeStampMixin):
    error_detail = models.TextField(null=True)
    nb_visited_links = models.PositiveSmallIntegerField()
    nb_success_links = models.PositiveSmallIntegerField()
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='crawlings')


class Scraping(TimeStampMixin):
    confession_html = models.TextField(null=True, editable=False)
    nb_iterations = models.PositiveSmallIntegerField()
    page = models.OneToOneField('Page', on_delete=models.CASCADE, related_name='scraping')
    pruning = models.ForeignKey('Pruning', on_delete=models.SET_NULL, related_name='scrapings',
                                null=True)

    def has_been_pruned(self) -> bool:
        return not self.confession_html or self.pruning is not None


class Pruning(TimeStampMixin):
    # We can not set unique=True because size can exceed index limits
    extracted_html = models.TextField(editable=False)
    extracted_html_hash = models.CharField(max_length=32, unique=True, editable=False)
    pruned_indices = ArrayField(models.PositiveSmallIntegerField(), null=True)
    pruned_html = models.TextField(null=True)

    def save(self, *args, **kwargs):
        self.extracted_html_hash = hash_string_to_hex(self.extracted_html)
        super().save(*args, **kwargs)


class Sentence(TimeStampMixin):
    class Action(models.TextChoices):
        SHOW = "show"
        HIDE = "hide"
        STOP = "stop"

    class Source(models.TextChoices):
        HUMAN = "human"
        ML = 'ml'

    line = models.TextField(null=False, unique=True)
    updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    pruning = models.ForeignKey('Pruning', on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=4, choices=Action)
    source = models.CharField(max_length=5, choices=Source)
    classifier = models.ForeignKey('Classifier', on_delete=models.SET_NULL,
                                   related_name='sentences', null=True)
    transformer_name = models.CharField(max_length=100)
    embedding = VectorField(dimensions=768)


class Classifier(TimeStampMixin):
    class Status(models.TextChoices):
        DRAFT = "draft"
        PROD = "prod"

    transformer_name = models.CharField(max_length=100)
    status = models.CharField(max_length=5, choices=Status)
    pickle = models.CharField()
    accuracy = models.FloatField()
