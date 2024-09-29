import uuid
from typing import List, Optional

from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.db import models
from pgvector.django import VectorField
from simple_history.models import HistoricalRecords

from home.utils.hash_utils import hash_string_to_hex
from scraping.parse.periods import PeriodEnum


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
    pruning_validation_counter = models.SmallIntegerField(default=0)
    pruning_last_validated_at = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()

    _pages = None
    _latest_crawling = None
    _has_search_latest_crawling = False

    def __str__(self):
        return self.name

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
        return all(map(lambda p: p.has_been_scraped(), self.get_pages()))

    def one_page_has_confessions(self) -> bool:
        return any(map(lambda p: p.has_confessions(), self.get_pages()))

    def all_pages_parsed(self) -> bool:
        return all(map(lambda p: p.has_been_parsed(), self.get_pages()))

    def delete_if_no_parish(self):
        if not self.parishes.exists():
            self.delete()

    def get_all_parsings(self) -> list['Parsing']:
        return [page.get_parsing() for page in self.get_pages() if page.has_been_parsed()]


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
    url = models.URLField()
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='pages')
    pruning_validation_counter = models.SmallIntegerField(default=0)
    pruning_last_validated_at = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        unique_together = ('url', 'website')

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

    def has_been_parsed(self) -> bool:
        return self.get_parsing() is not None

    def has_confessions(self) -> bool:
        return self.get_latest_pruning() is not None\
            and self.get_latest_pruning().pruned_html is not None

    def get_latest_pruning(self) -> Optional['Pruning']:
        if self.get_latest_scraping() is None:
            return None

        return self.get_latest_scraping().pruning

    def get_parsing(self) -> Optional['Parsing']:
        if self.get_latest_pruning() is None:
            return None

        return self.get_latest_pruning().parsings.filter(website=self.website).first()


class Crawling(TimeStampMixin):
    error_detail = models.TextField(null=True)
    nb_visited_links = models.PositiveSmallIntegerField()
    nb_success_links = models.PositiveSmallIntegerField()
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='crawlings')


class Scraping(TimeStampMixin):
    nb_iterations = models.PositiveSmallIntegerField()
    page = models.OneToOneField('Page', on_delete=models.CASCADE, related_name='scraping')
    pruning = models.ForeignKey('Pruning', on_delete=models.SET_NULL, related_name='scrapings',
                                null=True)  # can be null if extracted_html is None


class Pruning(TimeStampMixin):
    # We can not set unique=True because size can exceed index limits
    extracted_html = models.TextField(editable=False)
    extracted_html_hash = models.CharField(max_length=32, unique=True, editable=False)
    pruned_indices = ArrayField(models.PositiveSmallIntegerField(), null=True)
    pruned_html = models.TextField(null=True)
    history = HistoricalRecords()

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
    history = HistoricalRecords()


class Classifier(TimeStampMixin):
    class Status(models.TextChoices):
        DRAFT = "draft"
        PROD = "prod"

    transformer_name = models.CharField(max_length=100)
    status = models.CharField(max_length=5, choices=Status)
    pickle = models.CharField()
    accuracy = models.FloatField()
    history = HistoricalRecords()


class Parsing(TimeStampMixin):
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='parsings')
    pruning = models.ForeignKey('Pruning', on_delete=models.CASCADE, related_name='parsings')
    church_desc_by_id = models.JSONField()
    llm_model = models.CharField(max_length=100)
    prompt_template_hash = models.CharField(max_length=32)
    error_detail = models.TextField(null=True, blank=True)
    possible_by_appointment = models.BooleanField(null=True)
    is_related_to_mass = models.BooleanField(null=True)
    is_related_to_adoration = models.BooleanField(null=True)
    is_related_to_permanence = models.BooleanField(null=True)
    will_be_seasonal_events = models.BooleanField(null=True)
    history = HistoricalRecords()

    class Meta:
        unique_together = ('website', 'pruning')


class Schedule(TimeStampMixin):
    parsing = models.ForeignKey('Parsing', on_delete=models.CASCADE, related_name='schedules')
    church_id = models.SmallIntegerField(null=True)
    rrule = models.TextField(null=True, blank=True)  # in order to have TextArea in admin
    duration_in_minutes = models.SmallIntegerField(null=True)
    include_periods = ArrayField(models.CharField(max_length=16), choices=PeriodEnum.choices())
    exclude_periods = ArrayField(models.CharField(max_length=16), choices=PeriodEnum.choices())
    history = HistoricalRecords()
