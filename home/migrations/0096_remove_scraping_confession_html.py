# Generated by Django 5.0.8 on 2024-08-28 11:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0095_historicalwebsite_last_validated_at_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scraping',
            name='confession_html',
        ),
    ]
