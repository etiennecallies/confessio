from home.models.base_models import TimeStampMixin
from django.db import models


class ChurchLLMName(TimeStampMixin):
    church = models.ForeignKey('Church', on_delete=models.CASCADE, related_name='llm_names')
    prompt_template_hash = models.CharField(max_length=64)
    original_name = models.CharField(max_length=255)
    new_name = models.CharField(max_length=255, null=True)

    class Meta:
        unique_together = ('church', 'prompt_template_hash')


class ChurchTrouverUneMesse(TimeStampMixin):
    trouverunemesse_id = models.UUIDField(unique=True)
    trouverunemesse_slug = models.CharField(max_length=200, unique=True)
    original_name = models.CharField(max_length=255)


class ChurchTrouverUneMesseLLMName(TimeStampMixin):
    trouverunemesse_church = models.ForeignKey('ChurchTrouverUneMesse',
                                               on_delete=models.CASCADE,
                                               related_name='llm_names')
    prompt_template_hash = models.CharField(max_length=64)
    original_name = models.CharField(max_length=255)
    new_name = models.CharField(max_length=255, null=True)

    class Meta:
        unique_together = ('trouverunemesse_church', 'prompt_template_hash')
