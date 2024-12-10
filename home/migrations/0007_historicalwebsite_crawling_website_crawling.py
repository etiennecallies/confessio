# Generated by Django 5.0.9 on 2024-12-02 14:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_rename_website_crawling_website_temp'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalwebsite',
            name='crawling',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='home.crawling'),
        ),
        migrations.AddField(
            model_name='website',
            name='crawling',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='website', to='home.crawling'),
        ),
    ]