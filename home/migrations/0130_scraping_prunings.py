# Generated by Django 5.0.9 on 2024-11-17 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0129_alter_historicalwebsite_unreliability_reason_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='scraping',
            name='prunings',
            field=models.ManyToManyField(related_name='new_scrapings', to='home.pruning'),
        ),
    ]