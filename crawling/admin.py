from django.contrib import admin
from django.contrib.admin import ModelAdmin

from crawling.models import Log


@admin.register(Log)
class LogAdmin(ModelAdmin):
    list_display = ["website", "type", "status", "created_at",
                    "nb_visited_links", "nb_success_links"]
    list_filter = ["type", "status"]
    list_select_related = ["website"]
    ordering = ["-created_at"]
    fields = ["website", "type", "status", "started_at", "end_at",
              "nb_visited_links", "nb_success_links", "error_detail", "content"]
    readonly_fields = fields

    def has_add_permission(self, request):
        return False
