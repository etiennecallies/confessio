# Generated by Django 5.0.3 on 2024-04-23 16:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0048_rename_parish_page_website_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='crawling',
            old_name='parish',
            new_name='website',
        ),
    ]