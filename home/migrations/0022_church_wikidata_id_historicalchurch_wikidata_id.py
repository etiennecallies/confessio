# Generated by Django 5.0.11 on 2025-02-10 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0021_churchmoderation_diocese_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='church',
            name='wikidata_id',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='historicalchurch',
            name='wikidata_id',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
    ]
