# Generated by Django 5.0.8 on 2024-08-23 08:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0093_alter_historicalwebsitemoderation_category_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='page',
            options={},
        ),
        migrations.AlterUniqueTogether(
            name='page',
            unique_together={('url', 'website')},
        ),
    ]