from django.contrib import admin
from django.contrib.admin import ModelAdmin

from scheduling.models.pruning_models import Classifier, Sentence


@admin.register(Classifier)
class ClassifierAdmin(ModelAdmin):
    list_display = ["uuid", "status", "target", "created_at", "accuracy", 'test_size']
    ordering = ["-created_at"]
    fields = ['status']


@admin.register(Sentence)
class SentenceAdmin(ModelAdmin):
    list_display = ["line", "action", "human_temporal", "human_confession"]
    fields = ["line", 'action', "human_temporal", "human_confession"]
