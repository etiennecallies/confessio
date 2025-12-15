from django.db import models
from simple_history.models import HistoricalRecords

from home.models import TimeStampMixin
from scraping.parse.llm_client import LLMProvider


class OClocherOrganization(TimeStampMixin):
    organization_id = models.CharField(max_length=32, unique=True)
    website = models.OneToOneField('home.Website', on_delete=models.CASCADE,
                                   related_name='oclocher_organization')
    matching = models.OneToOneField('fetching.OClocherMatching', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='organization')


class OClocherLocation(TimeStampMixin):
    location_id = models.CharField(max_length=32, unique=True)
    organization = models.ForeignKey(OClocherOrganization, on_delete=models.CASCADE,
                                     related_name='locations')
    name = models.CharField(max_length=120)
    content = models.CharField(max_length=120, null=True, blank=True)
    address = models.CharField(max_length=120, null=True, blank=True)


class OClocherMatching(TimeStampMixin):
    church_desc_by_id = models.JSONField(editable=False)
    location_desc_by_id = models.JSONField(editable=False)

    llm_matrix = models.JSONField(null=True, blank=True)
    llm_provider = models.CharField(choices=LLMProvider.choices())
    llm_model = models.CharField(max_length=100)
    prompt_template_hash = models.CharField(max_length=32)
    llm_error_detail = models.TextField(null=True, blank=True)

    human_matrix = models.JSONField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        unique_together = ('church_desc_by_id', 'location_desc_by_id')


class OClocherSchedule(TimeStampMixin):
    schedule_id = models.CharField(max_length=32, unique=True)
    organization = models.ForeignKey(OClocherOrganization, on_delete=models.CASCADE,
                                     related_name='schedules')
    location = models.ForeignKey(OClocherLocation, on_delete=models.CASCADE,
                                 related_name='schedules')
    name = models.CharField(max_length=120)
    selection = models.CharField(max_length=16)
    datetime_start = models.DateTimeField()
    datetime_end = models.DateTimeField()
    recurrence_id = models.UUIDField(null=True, blank=True)

    history = HistoricalRecords()
