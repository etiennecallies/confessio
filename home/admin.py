from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.gis.admin import OSMGeoAdmin
from django.forms import ModelChoiceField

from .models import Church, Parish, Page


# Register your models here.


@admin.register(Parish)
class ParishAdmin(ModelAdmin):
    list_display = ["name"]


@admin.register(Church)
class ChurchAdmin(OSMGeoAdmin):
    list_display = ["name"]


# https://books.agiliq.com/projects/django-admin-cookbook/en/latest/fk_display.html
class ParishChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "Parish: {}".format(obj.name)


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
