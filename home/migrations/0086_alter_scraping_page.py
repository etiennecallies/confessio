# Generated by Django 5.0.7 on 2024-08-05 06:14

import django.db.models.deletion
from django.db import migrations, models


def keep_only_latest_scraping(apps, schema_editor):
    Page = apps.get_model('home', 'Page')
    for page in Page.objects.all():
        latest_scraping = page.scrapings.order_by('-created_at').first()
        page.scrapings.exclude(uuid=latest_scraping.uuid).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0085_pruning_extracted_html_hash_and_more'),
    ]

    operations = [
        migrations.RunPython(keep_only_latest_scraping),
        migrations.AlterField(
            model_name='scraping',
            name='page',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='scraping', to='home.page'),
        ),
    ]
