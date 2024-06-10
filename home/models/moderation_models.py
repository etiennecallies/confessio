from abc import abstractmethod
from typing import Optional

from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.db.models import Count
from django.db.models.functions import Now
from django.urls import reverse

from home.models.base_models import TimeStampMixin, Church, Parish

BUG_DESCRIPTION_MAX_LENGTH = 200


class ModerationMixin(TimeStampMixin):
    @property
    @abstractmethod
    def resource(self):
        pass

    validated_at = models.DateTimeField(null=True)
    marked_as_bug_at = models.DateTimeField(null=True)
    bug_description = models.CharField(max_length=BUG_DESCRIPTION_MAX_LENGTH, null=True,
                                       default=None)

    @property
    @abstractmethod
    def validated_by(self):
        pass

    @validated_by.setter
    @abstractmethod
    def validated_by(self, validated_by):
        pass

    @property
    @abstractmethod
    def marked_as_bug_by(self):
        pass

    @marked_as_bug_by.setter
    @abstractmethod
    def marked_as_bug_by(self, marked_as_bug_by):
        pass

    @property
    @abstractmethod
    def category(self):
        pass

    class Meta:
        abstract = True

    @classmethod
    def get_category_stat(cls, stat, is_bug: bool, count: int):
        return {
            'resource': cls.resource,
            'url': reverse('moderate_next_' + str(cls.resource),
                           kwargs={'category': stat['category'], 'is_bug': is_bug}),
            'category': stat['category'],
            'is_bug': is_bug,
            'total': count,
        }

    @classmethod
    def get_stats_by_category(cls):
        stats = []
        query_stats = cls.objects.filter(validated_at__isnull=True).all().values('category')\
            .annotate(total_count=Count('category'), bug_count=Count('marked_as_bug_at'))
        for stat in query_stats:
            if stat['bug_count']:
                stats.append(cls.get_category_stat(stat, is_bug=True, count=stat['bug_count']))
            if stat['total_count'] - stat['bug_count']:
                stats.append(cls.get_category_stat(stat, is_bug=False,
                                                   count=stat['total_count'] - stat['bug_count']))

        return stats

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

    def mark_as_bug(self, user: User, bug_description: Optional[str]):
        self.marked_as_bug_at = Now()
        self.marked_as_bug_by = user
        self.bug_description = bug_description
        self.save()


class ResourceDoesNotExist(Exception):
    pass


class WebsiteModeration(ModerationMixin):
    class Category(models.TextChoices):
        NAME_CONCATENATED = "name_concat"
        NAME_WEBSITE_TITLE = "name_websit"
        HOME_URL_NO_RESPONSE = "hu_no_resp"
        HOME_URL_NO_CONFESSION = "hu_no_conf"
        HOME_URL_CONFLICT = "hu_conflict"

    resource = 'website'
    validated_by = models.ForeignKey('auth.User', related_name=f'{resource}_validated_by',
                                     on_delete=models.SET_NULL, null=True)
    marked_as_bug_by = models.ForeignKey('auth.User', related_name=f'{resource}_marked_as_bug_by',
                                         on_delete=models.SET_NULL, null=True)
    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='moderations')
    category = models.CharField(max_length=11, choices=Category)

    home_url = models.URLField(null=True)
    other_website = models.ForeignKey('Website', on_delete=models.SET_NULL,
                                      related_name='other_moderations', null=True)

    class Meta:
        unique_together = ('website', 'category')

    def delete_on_validate(self) -> bool:
        # If website home_url has been changed, those moderation objects are not relevant any more
        if self.category in [self.Category.HOME_URL_NO_RESPONSE,
                             self.Category.HOME_URL_NO_CONFESSION]\
                and self.home_url != self.website.home_url:
            return True

        # If other_website has been merged, we can delete this moderation
        if self.category == self.Category.HOME_URL_CONFLICT\
                and self.other_website is None:
            return True

        if self.category in [self.Category.NAME_CONCATENATED, self.Category.NAME_WEBSITE_TITLE]:
            # There is no reasons to keep those
            return True

        # in other cases we keep this moderation
        return False


class ExternalSource(models.TextChoices):
    MESSESINFO = "messesinfo"
    LEHAVRE = "lehavre"


class ParishModeration(ModerationMixin):
    class Category(models.TextChoices):
        NAME_DIFFERS = "name_differs"
        WEBSITE_DIFFERS = "website_differs"
        ADDED_PARISH = "added_parish"
        DELETED_PARISH = "deleted_parish"

    resource = 'parish'
    validated_by = models.ForeignKey('auth.User', related_name=f'{resource}_validated_by',
                                     on_delete=models.SET_NULL, null=True)
    marked_as_bug_by = models.ForeignKey('auth.User', related_name=f'{resource}_marked_as_bug_by',
                                         on_delete=models.SET_NULL, null=True)
    parish = models.ForeignKey('Parish', on_delete=models.CASCADE, related_name='moderations')
    category = models.CharField(max_length=16, choices=Category)
    source = models.CharField(max_length=10, choices=ExternalSource)

    name = models.CharField(max_length=100, null=True)
    website = models.ForeignKey('Website', on_delete=models.CASCADE,
                                related_name='parish_moderations', null=True)
    similar_parishes = models.ManyToManyField('Parish', related_name='similar_moderations')

    class Meta:
        unique_together = ('parish', 'category', 'source')

    def delete_on_validate(self) -> bool:
        if self.category == self.Category.NAME_DIFFERS and self.parish.name == self.name:
            # Name has been replaced, we can delete
            return True

        if self.category == self.Category.WEBSITE_DIFFERS \
                and self.parish.website.home_url == self.website.home_url:
            # Website has been replaced, we can delete
            return True

        if self.category == self.Category.ADDED_PARISH:
            # In any case, we want to delete the moderation at validation
            return True

        # we need to keep moderations referring to external source diff
        return False

    def replace_website(self):
        previous_website = self.parish.website
        self.website.is_active = True
        self.website.save()
        self.parish.website = self.website
        self.parish.save()
        previous_website.delete_if_no_parish()

    def assign_external_id(self, similar_parish_uuid):
        try:
            similar_parish = Parish.objects.get(uuid=similar_parish_uuid)
        except Parish.DoesNotExist:
            raise ResourceDoesNotExist

        if self.source == ExternalSource.MESSESINFO:
            similar_parish.messesinfo_community_id = self.parish.messesinfo_community_id
        else:
            raise NotImplementedError

        parish_website = self.parish.website
        self.parish.delete()
        if parish_website:
            parish_website.delete_if_no_parish()
        similar_parish.save()
        # remove moderation PARISH_DELETED if exists
        ParishModeration.objects.filter(parish=similar_parish,
                                        category=self.Category.DELETED_PARISH,
                                        source=self.source).delete()


class ChurchModeration(ModerationMixin):
    class Category(models.TextChoices):
        LOCATION_NULL = "loc_null"
        LOCATION_FROM_API = "loc_api"
        NAME_DIFFERS = "name_differs"
        PARISH_DIFFERS = "parish_differs"
        LOCATION_DIFFERS = "location_differs"
        ADDED_CHURCH = "added_church"
        DELETED_CHURCH = "deleted_church"

    resource = 'church'
    validated_by = models.ForeignKey('auth.User', related_name=f'{resource}_validated_by',
                                     on_delete=models.SET_NULL, null=True)
    marked_as_bug_by = models.ForeignKey('auth.User', related_name=f'{resource}_marked_as_bug_by',
                                         on_delete=models.SET_NULL, null=True)
    church = models.ForeignKey('Church', on_delete=models.CASCADE, related_name='moderations')
    category = models.CharField(max_length=16, choices=Category)
    source = models.CharField(max_length=10, choices=ExternalSource)

    name = models.CharField(max_length=100, null=True)
    location = gis_models.PointField(geography=True, null=True)
    address = models.CharField(max_length=100, null=True)
    zipcode = models.CharField(max_length=5, null=True)
    city = models.CharField(max_length=50, null=True)
    parish = models.ForeignKey('Parish', on_delete=models.CASCADE,
                               related_name='church_moderations', null=True)

    similar_churches = models.ManyToManyField('Church', related_name='similar_moderations')

    class Meta:
        unique_together = ('church', 'category', 'source')

    def delete_on_validate(self) -> bool:
        # ephemeral moderations: we can safely delete
        if self.category in [self.Category.LOCATION_NULL, self.Category.LOCATION_FROM_API]:
            return True

        if self.category == self.Category.NAME_DIFFERS and self.church.name == self.name:
            # Name has been replaced, we can delete
            return True

        if self.category == self.Category.PARISH_DIFFERS and self.church.parish == self.parish:
            # Parish has been replaced, we can delete
            return True

        if self.category == self.Category.LOCATION_DIFFERS \
                and not self.location_desc_differs():
            # Location has been replaced, we can delete
            return True

        if self.category == self.Category.ADDED_CHURCH:
            # In any case, we want to delete the moderation at validation
            return True

        # we need to keep moderations referring to external source diff
        return False

    def location_desc_differs(self):
        return (self.location is not None and self.church.location != self.location) \
            or (self.address is not None and self.church.address != self.address) \
            or (self.zipcode is not None and self.church.zipcode != self.zipcode) \
            or (self.city is not None and self.church.city != self.city)

    def replace_name(self):
        self.church.name = self.name
        self.church.save()

    def replace_location(self):
        self.church.location = self.location
        self.church.save()

    def replace_address(self):
        self.church.address = self.address
        self.church.save()

    def replace_zipcode(self):
        self.church.zipcode = self.zipcode
        self.church.save()

    def replace_city(self):
        self.church.city = self.city
        self.church.save()

    def replace_parish(self):
        self.church.parish = self.parish
        self.church.save()

    def assign_external_id(self, similar_church_uuid):
        try:
            similar_church = Church.objects.get(uuid=similar_church_uuid)
        except Church.DoesNotExist:
            raise ResourceDoesNotExist

        if self.source == ExternalSource.MESSESINFO:
            similar_church.messesinfo_id = self.church.messesinfo_id
        else:
            raise NotImplementedError

        self.church.delete()
        similar_church.save()

        # remove moderation CHURCH_DELETED if exists
        ChurchModeration.objects.filter(church=similar_church,
                                        category=self.Category.DELETED_CHURCH,
                                        source=self.source).delete()


class ScrapingModeration(ModerationMixin):
    class Category(models.TextChoices):
        CONFESSION_HTML_PRUNED_NEW = "chp_new"

    resource = 'scraping'
    validated_by = models.ForeignKey('auth.User', related_name=f'{resource}_validated_by',
                                     on_delete=models.SET_NULL, null=True)
    marked_as_bug_by = models.ForeignKey('auth.User', related_name=f'{resource}_marked_as_bug_by',
                                         on_delete=models.SET_NULL, null=True)
    scraping = models.ForeignKey('Scraping', on_delete=models.SET_NULL, null=True,
                                 related_name='moderations')
    category = models.CharField(max_length=7, choices=Category)

    confession_html_pruned = models.TextField(null=False)

    class Meta:
        unique_together = ('scraping', 'category')

    def delete_on_validate(self) -> bool:
        # we keep ScrapingModeration even if confession_html_pruned has changed
        # in order to keep track of which confession_html_pruned has been moderated
        return False
