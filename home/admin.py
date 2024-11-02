from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.forms import ModelChoiceField
from leaflet.admin import LeafletGeoAdmin, LeafletGeoAdminMixin
from simple_history.admin import SimpleHistoryAdmin

from .models import Church, Website, Page, Diocese, Parish, Classifier, Sentence, Parsing, \
    OneOffSchedule, RegularSchedule


@admin.register(Diocese)
class DioceseAdmin(SimpleHistoryAdmin):
    list_display = ["name", "slug", "messesinfo_network_id"]


class ParishInline(admin.StackedInline):
    model = Parish


@admin.register(Website)
class WebsiteAdmin(SimpleHistoryAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    inlines = [
        ParishInline,
    ]


class ChurchInline(LeafletGeoAdminMixin, admin.StackedInline):
    model = Church


@admin.register(Parish)
class ParishAdmin(SimpleHistoryAdmin):
    list_display = ["name", "website"]
    search_fields = ["name"]
    autocomplete_fields = ["website"]
    inlines = [
        ChurchInline,
    ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'diocese':
            return DioceseChoiceField(queryset=Diocese.objects.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Church)
class ChurchAdmin(LeafletGeoAdmin, SimpleHistoryAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    display_raw = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'parish':
            return ParishChoiceField(queryset=Parish.objects.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Page)
class PageAdmin(ModelAdmin):
    list_display = ["url", "get_website_name"]

    @admin.display(ordering='website__name', description='Website')
    def get_website_name(self, obj):
        return obj.website.name

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'website':
            return WebsiteChoiceField(queryset=Website.objects.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# https://books.agiliq.com/projects/django-admin-cookbook/en/latest/fk_display.html
class WebsiteChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "Website: {}".format(obj.name)


class ParishChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "Parish: {}".format(obj.name)


class DioceseChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "Diocese: {}".format(obj.name)


@admin.register(Classifier)
class ClassifierAdmin(ModelAdmin):
    list_display = ["uuid", "status", "created_at", "accuracy", 'transformer_name']
    ordering = ["-created_at"]
    fields = ['status']


@admin.register(Sentence)
class SentenceAdmin(ModelAdmin):
    list_display = ["line", "action"]
    fields = ["line", 'action']


class OneOffScheduleInline(admin.StackedInline):
    model = OneOffSchedule


class RegularScheduleInline(admin.StackedInline):
    model = RegularSchedule


@admin.register(Parsing)
class ParsingAdmin(ModelAdmin):
    inlines = [
        OneOffScheduleInline,
        RegularScheduleInline
    ]
