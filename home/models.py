import uuid
from abc import abstractmethod
from typing import List, Optional

from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.db.models import Count
from django.db.models.functions import Now
from django.urls import reverse


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

    def all_pages_pruned(self) -> bool:
        return all(map(Page.latest_scraping_has_been_pruned, self.get_pages()))

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

    def latest_scraping_has_been_pruned(self) -> bool:
        return self.get_latest_scraping() is not None\
            and self.get_latest_scraping().has_been_pruned()

    def has_confessions(self) -> bool:
        return self.get_latest_scraping() is not None\
            and self.get_latest_scraping().confession_html_pruned


class Crawling(TimeStampMixin):
    error_detail = models.TextField(null=True)
    nb_visited_links = models.PositiveSmallIntegerField()
    nb_success_links = models.PositiveSmallIntegerField()
    parish = models.ForeignKey('Parish', on_delete=models.CASCADE, related_name='crawlings')


class Scraping(TimeStampMixin):
    confession_html = models.TextField(null=True)
    confession_html_pruned = models.TextField(null=True)
    pruned_at = models.DateTimeField(null=True)
    nb_iterations = models.PositiveSmallIntegerField()
    page = models.ForeignKey('Page', on_delete=models.CASCADE, related_name='scrapings')

    def has_been_pruned(self) -> bool:
        return self.pruned_at is not None


class Sentence(TimeStampMixin):
    line = models.TextField(null=False, unique=True)
    updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    scraping = models.ForeignKey('Scraping', on_delete=models.SET_NULL, null=True)
    is_confession = models.BooleanField()
    is_schedule = models.BooleanField()
    is_date = models.BooleanField()
    is_period = models.BooleanField()
    is_place = models.BooleanField()
    is_spiritual = models.BooleanField()
    is_other = models.BooleanField()


##############
# MODERATION #
##############

class ModerationMixin(TimeStampMixin):
    validated_at = models.DateTimeField(null=True)
    validated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)

    @property
    @abstractmethod
    def resource(self):
        pass

    @property
    @abstractmethod
    def category(self):
        pass

    class Meta:
        abstract = True

    @classmethod
    def get_stats_by_category(cls):
        return list(map(lambda d: d | {
            'resource': cls.resource,
            'url': reverse('moderate_next_' + str(cls.resource), kwargs={'category': d['category']})
        }, cls.objects.filter(validated_at__isnull=True).all()
                        .values('category').annotate(total=Count('category'))))

    def validate(self, user: User):
        if self.delete_on_validate():
            self.delete()
        else:
            self.validated_at = Now()
            self.validated_by = user
            self.save()

    @abstractmethod
    def delete_on_validate(self) -> bool:
        pass


class ParishModeration(ModerationMixin):
    class Category(models.TextChoices):
        NAME_CONCATENATED = "name_concat"
        NAME_WEBSITE_TITLE = "name_websit"
        HOME_URL_NO_RESPONSE = "hu_no_resp"
        HOME_URL_NO_CONFESSION = "hu_no_conf"

    resource = 'parish'
    parish = models.ForeignKey('Parish', on_delete=models.CASCADE, related_name='moderations')
    category = models.CharField(max_length=11, choices=Category)

    name = models.CharField(max_length=300)
    home_url = models.URLField()

    class Meta:
        unique_together = ('parish', 'category')

    def delete_on_validate(self) -> bool:
        # If parish home_url has been changed, those moderation objects are not relevant any more
        if self.category in [self.Category.HOME_URL_NO_RESPONSE,
                             self.Category.HOME_URL_NO_CONFESSION]\
                and self.home_url != self.parish.home_url:
            return True

        # for other categories we don't need to delete, we could though
        return False


class ChurchModeration(ModerationMixin):
    class Category(models.TextChoices):
        LOCATION_NULL = "loc_null"
        LOCATION_FROM_API = "loc_api"

    resource = 'church'
    church = models.ForeignKey('Church', on_delete=models.CASCADE, related_name='moderations')
    category = models.CharField(max_length=8, choices=Category)

    location = gis_models.PointField(geography=True)

    class Meta:
        unique_together = ('church', 'category')

    def delete_on_validate(self) -> bool:
        # we do not need to delete ChurchModeration, we could though
        return False


class ScrapingModeration(ModerationMixin):
    class Category(models.TextChoices):
        CONFESSION_HTML_PRUNED_NEW = "chp_new"

    resource = 'scraping'
    scraping = models.ForeignKey('Scraping', on_delete=models.CASCADE, related_name='moderations')
    category = models.CharField(max_length=7, choices=Category)

    confession_html_pruned = models.TextField(null=False)

    class Meta:
        unique_together = ('scraping', 'category')

    def delete_on_validate(self) -> bool:
        # we keep ScrapingModeration even if confession_html_pruned has changed
        # in order to keep track of which confession_html_pruned has been moderated
        return False
