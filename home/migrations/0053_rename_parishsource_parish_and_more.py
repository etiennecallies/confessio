# Generated by Django 5.0.3 on 2024-04-24 06:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0052_rename_other_parish_websitemoderation_other_website_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ParishSource',
            new_name='Parish',
        ),
        migrations.RenameField(
            model_name='church',
            old_name='parish_source',
            new_name='parish',
        ),
    ]
