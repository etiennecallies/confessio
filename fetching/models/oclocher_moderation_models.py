from django.db import models
from simple_history.models import HistoricalRecords

from registry.models.base_moderation_models import ModerationMixin


class OClocherOrganizationModeration(ModerationMixin):
    class Category(models.TextChoices):
        MULTIPLE_WIDGETS = "mutliple_widgets"
        SHARED_WIDGET = "shared_widget"
        NOT_FOUND = "not_found"

    resource = 'oclocher_organization'
    validated_by = models.ForeignKey('auth.User', related_name=f'{resource}_validated_by',
                                     on_delete=models.SET_NULL, null=True)
    marked_as_bug_by = models.ForeignKey('auth.User', related_name=f'{resource}_marked_as_bug_by',
                                         on_delete=models.SET_NULL, null=True)
    diocese = models.ForeignKey('registry.Diocese', on_delete=models.CASCADE,
                                related_name=f'{resource}_moderations')
    history = HistoricalRecords()
    category = models.CharField(max_length=32, choices=Category)

    website = models.ForeignKey('registry.Website', on_delete=models.CASCADE,
                                related_name='oclocher_organization_moderations')
    oclocher_organization = models.ForeignKey('OClocherOrganization',
                                              on_delete=models.SET_NULL, related_name='moderations',
                                              null=True)

    class Meta:
        unique_together = ('website', 'category')

    def delete_on_validate(self) -> bool:
        return False


class OClocherMatchingModeration(ModerationMixin):
    class Category(models.TextChoices):
        LLM_ERROR = "llm_error"
        CHURCHES_MISSING = "churches_missing"
        OK = "ok"

    resource = 'oclocher_matching'
    validated_by = models.ForeignKey('auth.User', related_name=f'{resource}_validated_by',
                                     on_delete=models.SET_NULL, null=True)
    marked_as_bug_by = models.ForeignKey('auth.User', related_name=f'{resource}_marked_as_bug_by',
                                         on_delete=models.SET_NULL, null=True)
    diocese = models.ForeignKey('registry.Diocese', on_delete=models.CASCADE,
                                related_name=f'{resource}_moderations')
    history = HistoricalRecords()
    category = models.CharField(max_length=16, choices=Category)

    oclocher_matching = models.OneToOneField('OClocherMatching',
                                             on_delete=models.CASCADE, related_name='moderation')
    oclocher_organization = models.ForeignKey('OClocherOrganization',
                                              on_delete=models.SET_NULL,
                                              related_name='matching_moderations', null=True)

    def delete_on_validate(self) -> bool:
        return False
