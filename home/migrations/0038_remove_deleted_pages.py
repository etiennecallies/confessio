# Generated by Django 5.0.3 on 2024-04-08 18:56

from django.db import migrations


def delete_pages_with_deleted_at_not_null(apps, schema_editor):
    apps.get_model('home', 'Page').objects.filter(deleted_at__isnull=False).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0037_parishmoderation_other_parish_alter_church_address_and_more'),
    ]

    operations = [
        migrations.RunPython(delete_pages_with_deleted_at_not_null),
    ]
