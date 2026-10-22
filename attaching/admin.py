from django.contrib import admin
from django.contrib.admin import ModelAdmin

from attaching.models import FileNote, FileNoteComment, Image


@admin.register(Image)
class ImageAdmin(ModelAdmin):
    list_display = ['website', 'name', 'comment', 'created_at']
    fields = ['name', 'comment', 'human_html', 'llm_html', ]


class FileNoteCommentInline(admin.TabularInline):
    model = FileNoteComment
    fields = ['content', 'user', 'created_at']
    readonly_fields = ['user', 'created_at']
    extra = 0


@admin.register(FileNote)
class FileNoteAdmin(ModelAdmin):
    list_display = ['website', 'name', 'caption', 'status', 'expire_at', 'created_at']
    fields = ['name', 'caption', 'status', 'expire_at', 'human_html', 'llm_html']
    inlines = [FileNoteCommentInline]
