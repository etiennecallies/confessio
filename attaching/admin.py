from django.contrib import admin
from django.contrib.admin import ModelAdmin

from attaching.models import Image


@admin.register(Image)
class ImageAdmin(ModelAdmin):
    list_display = ['website', 'name', 'comment', 'created_at']
    fields = ['name', 'comment', 'human_html', 'llm_html', ]
