from django.contrib import admin
from django.contrib.admin import ModelAdmin

from fetching.models import OClocherMatching


@admin.register(OClocherMatching)
class OClocherMatchingAdmin(ModelAdmin):
    list_display = ['church_desc_by_id_hash', 'llm_matrix', 'llm_error_detail', 'human_matrix']
    fields = ['human_matrix']
