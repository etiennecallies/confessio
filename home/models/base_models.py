import uuid
from datetime import timedelta
from typing import List, Optional

from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from pgvector.django import VectorField
from simple_history.models import HistoricalRecords, HistoricForeignKey

from home.models.custom_fields import ChoiceArrayField
from home.utils.hash_utils import hash_string_to_hex
from scraping.parse.periods import PeriodEnum, LiturgicalDayEnum
from scraping.prune.models import Action, Source


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
    class UnreliabilityReason(models.TextChoices):
        SCHEDULE_IN_IMAGE = "schedule_in_image"
        JAVASCRIPT_REQUIRED = "javascript_required"
        NOT_RESPONDING_AT_ALL = "not_responding_at_all"
        NOT_RESPONDING_IN_TIME = "not_responding_in_time"
        NOT_RESPONDING_200 = "not_responding_200"

    name = models.CharField(max_length=300)
    home_url = models.URLField(unique=True)
    is_active = models.BooleanField(default=True)
    crawling = models.OneToOneField('Crawling', on_delete=models.SET_NULL,
                                    related_name='website', null=True)
    pruning_validation_counter = models.SmallIntegerField(default=0)
    pruning_last_validated_at = models.DateTimeField(null=True, blank=True)
    parsing_validation_counter = models.SmallIntegerField(default=0)
    parsing_last_validated_at = models.DateTimeField(null=True, blank=True)
    unreliability_reason = models.CharField(choices=UnreliabilityReason, null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def has_been_crawled(self) -> bool:
        return self.crawling is not None

    def get_pages(self) -> List['Page']:
        return self.pages.all()

    def has_pages(self) -> bool:
        return len(self.get_pages()) > 0

    def all_pages_scraped(self) -> bool:
        return all(map(lambda p: p.has_been_scraped(), self.get_pages()))

    def one_page_has_confessions(self) -> bool:
        return any(map(lambda p: p.has_confessions(), self.get_pages()))

    def all_pages_parsed(self) -> bool:
        return all(map(lambda page: page.has_been_parsed(), self.get_pages()))

    def delete_if_no_parish(self):
        if not self.parishes.exists():
            self.delete()

    def get_all_parsings(self) -> list['Parsing']:
        all_parsings = [page.get_parsing(pruning)
                        for page in self.get_pages()
                        for pruning in page.get_prunings()]
        return [p for p in all_parsings if p is not None]

    def get_church_desc_by_id(self) -> dict[int, str]:
        church_descs = []
        for parish in self.parishes.all():
            for church in parish.churches.all():
                church_descs.append(church.get_desc())

        church_desc_by_id = {}
        for i, desc in enumerate(sorted(church_descs)):
            church_desc_by_id[i] = desc

        return church_desc_by_id


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

    def get_desc(self) -> str:
        return f'{self.name} {self.city}'


class Page(TimeStampMixin):
    url = models.URLField()
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='pages')
    scraping = models.OneToOneField('Scraping', on_delete=models.SET_NULL, related_name='page',
                                    null=True)
    pruning_validation_counter = models.SmallIntegerField(default=0)
    pruning_last_validated_at = models.DateTimeField(null=True, blank=True)
    parsing_validation_counter = models.SmallIntegerField(default=0)
    parsing_last_validated_at = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        unique_together = ('url', 'website')

    def has_been_scraped(self) -> bool:
        return self.scraping is not None

    def has_been_parsed(self) -> bool:
        if self.get_prunings() is None:
            return False

        return all(pruning.has_been_parsed(self.website) for pruning in self.get_prunings())

    def has_confessions(self) -> bool:
        if self.get_prunings() is None:
            return False

        return any(pruning.has_confessions() for pruning in self.get_prunings())

    def get_prunings(self) -> list['Pruning'] or None:
        if self.scraping is None:
            return None

        return self.scraping.prunings.all()

    def get_parsing(self, pruning: 'Pruning') -> Optional['Parsing']:
        return pruning.get_parsing(self.website)

    def has_been_modified_recently(self) -> bool:
        if self.scraping is None:
            return False

        # If latest scraping was created more than one year ago
        if self.scraping.created_at < timezone.now() - timedelta(days=365):
            return False

        # If latest scraping is older than page creation
        if self.scraping.created_at <= self.created_at + timedelta(hours=2):
            return False

        return True


class Crawling(TimeStampMixin):
    error_detail = models.TextField(null=True)
    nb_visited_links = models.PositiveSmallIntegerField()
    nb_success_links = models.PositiveSmallIntegerField()
    website_temp = models.ForeignKey('Website', on_delete=models.CASCADE,
                                     related_name='crawlings')


class Scraping(TimeStampMixin):
    nb_iterations = models.PositiveSmallIntegerField()
    prunings = models.ManyToManyField('Pruning', related_name='scrapings')


class Pruning(TimeStampMixin):
    # We can not set unique=True because size can exceed index limits
    extracted_html = models.TextField(editable=False)
    extracted_html_hash = models.CharField(max_length=32, unique=True, editable=False)
    pruned_indices = ArrayField(models.PositiveSmallIntegerField(), null=True)
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        self.extracted_html_hash = hash_string_to_hex(self.extracted_html)
        super().save(*args, **kwargs)

    def has_confessions(self) -> bool:
        return bool(self.pruned_indices)

    def get_parsing(self, website: Website) -> Optional['Parsing']:
        for parsing in self.parsings.all():
            if parsing.match_website(website):
                return parsing

        return None

    def has_been_parsed(self, website: Website) -> bool:
        if not self.pruned_indices:
            # no parsing needed
            return True

        return self.get_parsing(website) is not None


class Sentence(TimeStampMixin):
    line = models.TextField(null=False, unique=True)
    updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    updated_on_pruning = models.ForeignKey('Pruning', on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=5, choices=Action.choices())
    source = models.CharField(max_length=5, choices=Source.choices())
    classifier = models.ForeignKey('Classifier', on_delete=models.SET_NULL,
                                   related_name='sentences', null=True)
    transformer_name = models.CharField(max_length=100)
    embedding = VectorField(dimensions=768)
    prunings = models.ManyToManyField('Pruning', related_name='sentences')
    history = HistoricalRecords()


class Classifier(TimeStampMixin):
    class Status(models.TextChoices):
        DRAFT = "draft"
        PROD = "prod"

    transformer_name = models.CharField(max_length=100)
    status = models.CharField(max_length=5, choices=Status)
    pickle = models.CharField()
    accuracy = models.FloatField()
    test_size = models.PositiveSmallIntegerField()
    history = HistoricalRecords()


class Parsing(TimeStampMixin):
    truncated_html = models.TextField(editable=False)
    truncated_html_hash = models.CharField(max_length=32, editable=False)
    church_desc_by_id = models.JSONField(editable=False)

    prunings = models.ManyToManyField('Pruning', related_name='parsings')

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
        unique_together = ('truncated_html_hash', 'church_desc_by_id')

    def get_schedules(self) -> list['Schedule']:
        return list(self.one_off_schedules.all()) + list(self.regular_schedules.all())

    def get_websites(self) -> list['Website']:
        return Website.objects.filter(pages__scraping__prunings__parsings=self).distinct()

    def match_website(self, website: Website) -> bool:
        return self.church_desc_by_id == website.get_church_desc_by_id()


class Schedule(TimeStampMixin):
    church_id = models.SmallIntegerField(null=True, blank=True)
    is_cancellation = models.BooleanField()
    start_time_iso8601 = models.CharField(max_length=8, null=True, blank=True)
    end_time_iso8601 = models.CharField(max_length=8, null=True, blank=True)

    class Meta:
        abstract = True


class OneOffSchedule(Schedule):
    parsing = HistoricForeignKey('Parsing', on_delete=models.CASCADE,
                                 related_name='one_off_schedules')
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    month = models.PositiveSmallIntegerField(null=True, blank=True)
    day = models.PositiveSmallIntegerField(null=True, blank=True)
    weekday_iso8601 = models.PositiveSmallIntegerField(null=True, blank=True)
    liturgical_day = models.CharField(max_length=16, null=True, blank=True,
                                      choices=LiturgicalDayEnum.choices())
    history = HistoricalRecords()


class RegularSchedule(Schedule):
    parsing = HistoricForeignKey('Parsing', on_delete=models.CASCADE,
                                 related_name='regular_schedules')
    rrule = models.TextField()  # in order to have TextArea in admin
    include_periods = ChoiceArrayField(models.CharField(max_length=16,
                                                        choices=PeriodEnum.choices()),
                                       blank=True)
    exclude_periods = ChoiceArrayField(models.CharField(max_length=16,
                                                        choices=PeriodEnum.choices()),
                                       blank=True)
    history = HistoricalRecords()
