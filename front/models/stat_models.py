from django.db import models

from core.models.base_models import TimeStampMixin


class SearchHit(TimeStampMixin):
    query = models.CharField(max_length=255)
    nb_websites = models.IntegerField()
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    user_agent = models.TextField(null=True)
    ip_address_hash = models.CharField(max_length=64, null=True)


class AutocompleteHit(TimeStampMixin):
    query = models.CharField(max_length=255)
    rank = models.PositiveSmallIntegerField()
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    item_type = models.CharField(max_length=255)
    item_name = models.CharField(max_length=255)
    item_context = models.CharField(max_length=255)
    item_latitude = models.FloatField(null=True)
    item_longitude = models.FloatField(null=True)
    item_uuid = models.CharField(max_length=255, null=True)
