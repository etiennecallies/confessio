import uuid

from django.contrib.gis.db import models as gis_models
from django.db import models


# Create your models here.


class TimeStampMixin(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Parish(TimeStampMixin):
    name = models.CharField(max_length=100)
    home_url = models.URLField()
    confession_hours_url = models.URLField()


class Church(TimeStampMixin):
    name = models.CharField(max_length=100)
    location = gis_models.PointField()
    address = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=5)
    city = models.CharField(max_length=50)
