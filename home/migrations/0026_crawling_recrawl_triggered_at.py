# Generated by Django 5.0.11 on 2025-03-03 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0025_historicalparsing_llm_provider_parsing_llm_provider'),
    ]

    operations = [
        migrations.AddField(
            model_name='crawling',
            name='recrawl_triggered_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
