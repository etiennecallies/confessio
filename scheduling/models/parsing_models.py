from home.models import ModerationMixin, TimeStampMixin
from django.db import models
from simple_history.models import HistoricalRecords

from scraping.parse.llm_client import LLMProvider


class Parsing(TimeStampMixin):
    truncated_html = models.TextField(editable=False)
    truncated_html_hash = models.CharField(max_length=32, editable=False)
    church_desc_by_id = models.JSONField(editable=False)

    llm_json = models.JSONField(null=True, blank=True)
    llm_json_version = models.CharField(max_length=6, default='v1.0')
    llm_provider = models.CharField(choices=LLMProvider.choices())
    llm_model = models.CharField(max_length=100)
    prompt_template_hash = models.CharField(max_length=32)
    llm_error_detail = models.TextField(null=True, blank=True)

    human_json = models.JSONField(null=True, blank=True)
    human_json_version = models.CharField(max_length=6, default='v1.0')

    history = HistoricalRecords(table_name='home_historicalparsing')

    class Meta:
        unique_together = ('truncated_html_hash', 'church_desc_by_id')
        db_table = "home_parsing"

    def has_been_moderated(self) -> bool:
        return self.human_json is not None


class ParsingModeration(ModerationMixin):
    class Category(models.TextChoices):
        NEW_SCHEDULES = "new_schedules"
        SCHEDULES_DIFFER = "schedules_differ"
        LLM_ERROR = "llm_error"

    resource = 'parsing'
    validated_by = models.ForeignKey('auth.User', related_name=f'{resource}_validated_by',
                                     on_delete=models.SET_NULL, null=True)
    marked_as_bug_by = models.ForeignKey('auth.User', related_name=f'{resource}_marked_as_bug_by',
                                         on_delete=models.SET_NULL, null=True)
    diocese = models.ForeignKey('home.Diocese', on_delete=models.CASCADE,
                                related_name=f'{resource}_moderations', null=True)
    history = HistoricalRecords()
    parsing = models.ForeignKey('Parsing', on_delete=models.CASCADE,
                                related_name='moderations')
    category = models.CharField(max_length=16, choices=Category)

    class Meta:
        unique_together = ('parsing', 'category')

    def delete_on_validate(self) -> bool:
        # we always keep validated ParsingModeration
        return False
