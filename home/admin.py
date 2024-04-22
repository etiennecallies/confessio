from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.forms import ModelChoiceField
from leaflet.admin import LeafletGeoAdmin

from .models import Church, Parish, Page, Diocese, ParishSource


@admin.register(Diocese)
class DioceseAdmin(ModelAdmin):
    list_display = ["name", "slug", "messesinfo_network_id"]


@admin.register(Parish)
class ParishAdmin(ModelAdmin):
    list_display = ["name"]


@admin.register(ParishSource)
class ParishSourceAdmin(ModelAdmin):
    list_display = ["name"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'diocese':
            return DioceseChoiceField(queryset=Diocese.objects.all())
        if db_field.name == 'parish':
            return ParishChoiceField(queryset=Parish.objects.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Church)
class ChurchAdmin(LeafletGeoAdmin):
    list_display = ["name"]
    display_raw = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'parish_source':
            return ParishSourceChoiceField(queryset=ParishSource.objects.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Page)
class PageAdmin(ModelAdmin):
    list_display = ["url", "get_parish_name"]

    @admin.display(ordering='parish__name', description='Parish')
    def get_parish_name(self, obj):
        return obj.parish.name

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'parish':
            return ParishChoiceField(queryset=Parish.objects.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# https://books.agiliq.com/projects/django-admin-cookbook/en/latest/fk_display.html
class ParishChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "Parish: {}".format(obj.name)


class ParishSourceChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "ParishSource: {}".format(obj.name)


class DioceseChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "Diocese: {}".format(obj.name)
