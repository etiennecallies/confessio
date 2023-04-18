from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from.models import Church, Parish

# Register your models here.


@admin.register(Parish)
class ParishAdmin(OSMGeoAdmin):
    pass


@admin.register(Church)
class ChurchAdmin(OSMGeoAdmin):
    pass
