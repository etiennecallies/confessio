# Generated by Django 5.0.9 on 2024-11-17 11:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0130_scraping_prunings'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scraping',
            name='pruning',
        ),
    ]