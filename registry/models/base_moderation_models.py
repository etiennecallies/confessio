from abc import abstractmethod
from typing import Optional

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
from django.db.models.functions import Now
from django.urls import reverse

from core.models.base_models import TimeStampMixin
from home.utils.color_utils import get_color_from_string
from registry.models import Diocese

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
    def diocese(self) -> Diocese | None:
        pass

    @diocese.setter
    @abstractmethod
    def diocese(self, diocese: Diocese | None):
        pass

    @property
    @abstractmethod
    def category(self):
        pass

    class Meta:
        abstract = True

    @classmethod
    def get_category_stat(cls, stat, is_bug: bool, diocese: Diocese | None, count: int):
        diocese_slug = diocese.slug if diocese else 'no_diocese'

        return {
            'resource': cls.resource,
            'url': reverse('moderate_next_' + str(cls.resource),
                           kwargs={'category': stat['category'], 'is_bug': is_bug,
                                   'diocese_slug': diocese_slug}),
            'category': stat['category'],
            'is_bug': is_bug,
            'total': count,
            'color': get_color_from_string(f"{cls.resource}{stat['category']}"),
        }

    @classmethod
    def get_stats_by_category(cls, diocese: Diocese | None):
        stats = []
        objects_filter = cls.objects.filter(validated_at__isnull=True)
        if diocese:
            objects_filter = objects_filter.filter(diocese=diocese)
        query_stats = objects_filter.all()\
            .values('category')\
            .annotate(total_count=Count('category'), bug_count=Count('marked_as_bug_at'))
        for stat in query_stats:
            if stat['bug_count']:
                stats.append(cls.get_category_stat(stat, is_bug=True, diocese=diocese,
                                                   count=stat['bug_count']))
            if stat['total_count'] - stat['bug_count']:
                stats.append(cls.get_category_stat(stat, is_bug=False, diocese=diocese,
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

    def get_diocese_slug(self) -> str:
        return self.diocese.slug if self.diocese else 'no_diocese'


class ResourceDoesNotExistError(Exception):
    pass
