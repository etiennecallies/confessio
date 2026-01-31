from django.db import models

from core.models.base_models import TimeStampMixin


class Scheduling(TimeStampMixin):
    class Status(models.TextChoices):
        BUILT = "built"
        PRUNED = "pruned"
        PARSED = "parsed"
        MATCHED = "matched"
        INDEXED = "indexed"

    website = models.ForeignKey('registry.Website', on_delete=models.CASCADE,
                                related_name='schedulings')
    status = models.CharField(max_length=16, choices=Status.choices)

    merged_schedules = models.JSONField(null=True, blank=True)


class SchedulingHistoricalChurch(TimeStampMixin):
    scheduling = models.ForeignKey('Scheduling', on_delete=models.CASCADE,
                                   related_name='historical_churches')
    church_history_id = models.PositiveIntegerField()

    class Meta:
        unique_together = ('scheduling', 'church_history_id')


class SchedulingHistoricalScraping(TimeStampMixin):
    scheduling = models.ForeignKey('Scheduling', on_delete=models.CASCADE,
                                   related_name='historical_scrapings')
    scraping_history_id = models.PositiveIntegerField()

    class Meta:
        unique_together = ('scheduling', 'scraping_history_id')


class SchedulingHistoricalImage(TimeStampMixin):
    scheduling = models.ForeignKey('Scheduling', on_delete=models.CASCADE,
                                   related_name='historical_images')
    image_history_id = models.PositiveIntegerField()

    class Meta:
        unique_together = ('scheduling', 'image_history_id')


class SchedulingHistoricalOClocherLocation(TimeStampMixin):
    scheduling = models.ForeignKey('Scheduling', on_delete=models.CASCADE,
                                   related_name='historical_oclocher_locations')
    oclocher_location_history_id = models.PositiveIntegerField()

    class Meta:
        unique_together = ('scheduling', 'oclocher_location_history_id')


class SchedulingHistoricalOClocherSchedule(TimeStampMixin):
    scheduling = models.ForeignKey('Scheduling', on_delete=models.CASCADE,
                                   related_name='historical_oclocher_schedules')
    oclocher_schedule_history_id = models.PositiveIntegerField()

    class Meta:
        unique_together = ('scheduling', 'oclocher_schedule_history_id')


class ScrapingPruning(TimeStampMixin):
    scheduling = models.ForeignKey('Scheduling', on_delete=models.CASCADE,
                                   related_name='scraping_prunings')
    scraping_history_id = models.PositiveIntegerField()
    pruning_history_id = models.PositiveIntegerField()

    class Meta:
        unique_together = ('scheduling', 'scraping_history_id', 'pruning_history_id')


class ImagePruning(TimeStampMixin):
    scheduling = models.ForeignKey('Scheduling', on_delete=models.CASCADE,
                                   related_name='image_prunings')
    image_history_id = models.PositiveIntegerField()
    pruning_history_id = models.PositiveIntegerField()

    class Meta:
        unique_together = ('scheduling', 'image_history_id', 'pruning_history_id')


class PruningParsing(TimeStampMixin):
    scheduling = models.ForeignKey('Scheduling', on_delete=models.CASCADE,
                                   related_name='pruning_parsings')
    pruning_history_id = models.PositiveIntegerField()
    parsing_history_id = models.PositiveIntegerField()

    class Meta:
        unique_together = ('scheduling', 'pruning_history_id', 'parsing_history_id')


class SchedulingHistoricalOClocherMatching(TimeStampMixin):
    scheduling = models.OneToOneField('Scheduling', on_delete=models.CASCADE,
                                      related_name='historical_oclocher_matching')
    oclocher_matching_history_id = models.PositiveIntegerField()
