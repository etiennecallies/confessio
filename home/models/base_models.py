import uuid
from datetime import timedelta
from typing import Optional

from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from pgvector.django import VectorField
from simple_history.models import HistoricalRecords

from home.utils.hash_utils import hash_string_to_hex
from scraping.extract_v2.models import EventMotion
from scraping.parse.llm_client import LLMProvider
from scraping.prune.models import Action, Source


class TimeStampMixin(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    class Meta:
        abstract = True
        get_latest_by = ['updated_at']


class Diocese(TimeStampMixin):
    name = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True)
    messesinfo_network_id = models.CharField(max_length=100, unique=True)
    home_url = models.URLField(unique=True, null=True, blank=True)
    history = HistoricalRecords()


class Website(TimeStampMixin):
    class UnreliabilityReason(models.TextChoices):
        SCHEDULE_IN_IMAGE = "schedule_in_image"
        SCHEDULE_IN_PDF = "schedule_in_pdf"
        JAVASCRIPT_REQUIRED = "javascript_required"
        TOO_NOISY_HTML = "too_noisy_html"
        NOT_RESPONDING_AT_ALL = "not_responding_at_all"
        NOT_RESPONDING_IN_TIME = "not_responding_in_time"
        NOT_RESPONDING_200 = "not_responding_200"
        FOREIGN_LANGUAGE = "foreign_language"

    name = models.CharField(max_length=300)
    home_url = models.URLField(unique=True)
    is_active = models.BooleanField(default=True)
    enabled_for_crawling = models.BooleanField(default=True)
    crawling = models.OneToOneField('Crawling', on_delete=models.SET_NULL,
                                    related_name='website', null=True, blank=True)
    pruning_validation_counter = models.SmallIntegerField(default=0)
    pruning_last_validated_at = models.DateTimeField(null=True, blank=True)
    parsing_validation_counter = models.SmallIntegerField(default=0)
    parsing_last_validated_at = models.DateTimeField(null=True, blank=True)
    unreliability_reason = models.CharField(choices=UnreliabilityReason, null=True, blank=True)
    nb_recent_hits = models.PositiveSmallIntegerField(default=0)
    is_best_diocese_hit = models.BooleanField(default=False)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def has_been_crawled(self) -> bool:
        return self.crawling_id is not None

    def get_pages(self) -> list['Page']:
        return list(self.pages.all())

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

    def get_church_desc_by_id(self) -> dict[int, str]:
        church_descs = []
        for parish in self.parishes.all():
            for church in parish.churches.all():
                church_descs.append(church.get_desc())

        church_desc_by_id = {}
        for i, desc in enumerate(sorted(church_descs)):
            church_desc_by_id[i] = desc

        return church_desc_by_id

    def get_diocese(self) -> Diocese | None:
        if not self.parishes.exists():
            return None

        return self.parishes.first().diocese

    async def async_get_diocese(self) -> Diocese | None:
        if not await self.parishes.aexists():
            return None

        first_parish = await self.parishes.select_related('diocese').afirst()
        return first_parish.diocese


class Parish(TimeStampMixin):
    name = models.CharField(max_length=100)
    messesinfo_network_id = models.CharField(max_length=100, null=True, blank=True)
    messesinfo_community_id = models.CharField(max_length=200, null=True, unique=True, blank=True)
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='parishes',
                                null=True, blank=True)
    diocese = models.ForeignKey('Diocese', on_delete=models.CASCADE, related_name='parishes')
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class Church(TimeStampMixin):
    name = models.CharField(max_length=120)
    location = gis_models.PointField(geography=True, null=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    zipcode = models.CharField(max_length=5, null=True)
    city = models.CharField(max_length=50, null=True)
    messesinfo_id = models.CharField(max_length=100, null=True, unique=True, blank=True)
    wikidata_id = models.CharField(max_length=100, null=True, unique=True, blank=True)
    trouverunemesse_id = models.UUIDField(null=True, unique=True, blank=True)
    trouverunemesse_slug = models.CharField(max_length=200, null=True, unique=True, blank=True)
    trouverunemesse_updated_at = models.DateTimeField(null=True, blank=True)
    parish = models.ForeignKey('Parish', on_delete=models.CASCADE,
                               related_name='churches')
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()

    def get_desc(self) -> str:
        return f'{self.name} {self.city}'


class WebsiteForbiddenPath(TimeStampMixin):
    website = models.ForeignKey('Website', on_delete=models.CASCADE,
                                related_name='forbidden_paths')
    path = models.CharField(max_length=300)

    class Meta:
        unique_together = ('website', 'path')


class Page(TimeStampMixin):
    url = models.URLField(max_length=300)
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='pages')
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
    recrawl_triggered_at = models.DateTimeField(null=True, blank=True)


class Scraping(TimeStampMixin):
    nb_iterations = models.PositiveSmallIntegerField()
    prunings = models.ManyToManyField('Pruning', related_name='scrapings')
    page = models.OneToOneField('Page', on_delete=models.CASCADE, related_name='scraping')


class Pruning(TimeStampMixin):
    # We can not set unique=True because size can exceed index limits
    extracted_html = models.TextField(editable=False)
    extracted_html_hash = models.CharField(max_length=32, unique=True, editable=False)
    pruned_indices = ArrayField(models.PositiveSmallIntegerField(), null=True)
    ml_indices = ArrayField(models.PositiveSmallIntegerField(), null=True)
    human_indices = ArrayField(models.PositiveSmallIntegerField(), null=True)
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
        if not self.has_confessions():
            # no parsing needed
            return True

        return self.get_parsing(website) is not None

    def get_diocese(self) -> Diocese | None:
        if not self.scrapings.exists():
            return None

        return self.scrapings.first().page.website.get_diocese()


class Sentence(TimeStampMixin):
    line = models.TextField(null=False, unique=True)
    prunings = models.ManyToManyField('Pruning', related_name='sentences')
    updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    updated_on_pruning = models.ForeignKey('Pruning', on_delete=models.SET_NULL, null=True)
    transformer_name = models.CharField(max_length=100)
    embedding = VectorField(dimensions=768)
    # v1
    action = models.CharField(max_length=5, choices=Action.choices())
    source = models.CharField(max_length=5, choices=Source.choices())
    classifier = models.ForeignKey('Classifier', on_delete=models.SET_NULL,
                                   related_name='sentences', null=True)
    # v2
    ml_specifier = models.BooleanField(null=True)
    human_specifier = models.BooleanField(null=True)
    specifier_classifier = models.ForeignKey('Classifier', on_delete=models.SET_NULL,
                                             related_name='specifier_sentences', null=True)
    ml_schedule = models.BooleanField(null=True)
    human_schedule = models.BooleanField(null=True)
    schedule_classifier = models.ForeignKey('Classifier', on_delete=models.SET_NULL,
                                            related_name='schedule_sentences', null=True)
    ml_confession = models.CharField(max_length=5, choices=EventMotion.choices(), null=True)
    human_confession = models.CharField(max_length=5, choices=EventMotion.choices(), null=True)
    confession_classifier = models.ForeignKey('Classifier', on_delete=models.SET_NULL,
                                              related_name='confession_sentences', null=True)
    history = HistoricalRecords()


def default_different_labels():
    return Action.list_items()


class Classifier(TimeStampMixin):
    class Status(models.TextChoices):
        DRAFT = "draft"
        PROD = "prod"

    class Target(models.TextChoices):
        # V1
        ACTION = "action"
        # V2
        SPECIFIER = "specifier"
        SCHEDULE = "schedule"
        CONFESSION = "confession"

    transformer_name = models.CharField(max_length=100)
    status = models.CharField(max_length=5, choices=Status)
    target = models.CharField(max_length=10, choices=Target, default=Target.ACTION)
    different_labels = models.JSONField(default=default_different_labels)
    pickle = models.CharField()
    accuracy = models.FloatField()
    test_size = models.PositiveSmallIntegerField()
    history = HistoricalRecords()


class Parsing(TimeStampMixin):
    truncated_html = models.TextField(editable=False)
    truncated_html_hash = models.CharField(max_length=32, editable=False)
    church_desc_by_id = models.JSONField(editable=False)

    prunings = models.ManyToManyField('Pruning', related_name='parsings')
    website = models.ForeignKey('Website', on_delete=models.SET_NULL, related_name='parsings',
                                null=True)

    llm_json = models.JSONField(null=True, blank=True)
    llm_provider = models.CharField(choices=LLMProvider.choices())
    llm_model = models.CharField(max_length=100)
    prompt_template_hash = models.CharField(max_length=32)
    llm_error_detail = models.TextField(null=True, blank=True)

    human_json = models.JSONField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        unique_together = ('truncated_html_hash', 'church_desc_by_id')

    def match_website(self, website: Website) -> bool:
        return set(self.church_desc_by_id.values()) == set(website.get_church_desc_by_id().values())

    def has_been_moderated(self) -> bool:
        return self.human_json is not None


class Image(TimeStampMixin):
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='images')
    name = models.CharField(max_length=256)
    comment = models.TextField(null=True, blank=True)
    llm_html = models.TextField(null=True, blank=True)
    llm_provider = models.CharField(choices=LLMProvider.choices(), null=True, blank=True)
    llm_model = models.CharField(max_length=100, null=True, blank=True)
    prompt_hash = models.CharField(max_length=32, null=True, blank=True)
    llm_error_detail = models.TextField(null=True, blank=True)
    human_html = models.TextField(null=True, blank=True)
    prunings = models.ManyToManyField('Pruning', related_name='images')
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    user_agent = models.TextField(null=True, blank=True)
    ip_address_hash = models.CharField(max_length=64, null=True, blank=True)
