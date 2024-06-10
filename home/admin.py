from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.forms import ModelChoiceField
from leaflet.admin import LeafletGeoAdmin

from .models import Church, Website, Page, Diocese, Parish


@admin.register(Diocese)
class DioceseAdmin(ModelAdmin):
    list_display = ["name", "slug", "messesinfo_network_id"]


class ParishInline(admin.StackedInline):
    model = Parish


@admin.register(Website)
class WebsiteAdmin(ModelAdmin):
    list_display = ["name"]
    inlines = [
        ParishInline,
    ]


@admin.register(Parish)
class ParishAdmin(ModelAdmin):
    list_display = ["name"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'diocese':
            return DioceseChoiceField(queryset=Diocese.objects.all())
        if db_field.name == 'website':
            return WebsiteChoiceField(queryset=Website.objects.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Church)
class ChurchAdmin(LeafletGeoAdmin):
    list_display = ["name"]
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
