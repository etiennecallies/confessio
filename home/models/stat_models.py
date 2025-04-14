from home.models.base_models import TimeStampMixin
from django.db import models


class SearchHit(TimeStampMixin):
    query = models.CharField(max_length=255)
    nb_websites = models.IntegerField()
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    user_agent = models.TextField(null=True)
    ip_address_hash = models.CharField(max_length=64, null=True)


class Log(TimeStampMixin):
    class Type(models.TextChoices):
        CRAWLING = "crawling"
        SCRAPING = "scraping"

    website = models.ForeignKey('Website', on_delete=models.CASCADE, related_name='logs')
    content = models.TextField()
    type = models.CharField(max_length=8, choices=Type)
