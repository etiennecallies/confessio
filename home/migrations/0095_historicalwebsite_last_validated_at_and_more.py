# Generated by Django 5.0.8 on 2024-08-27 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0094_alter_page_options_alter_page_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalwebsite',
            name='last_validated_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='historicalwebsite',
            name='validation_counter',
            field=models.SmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='website',
            name='last_validated_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='website',
            name='validation_counter',
            field=models.SmallIntegerField(default=0),
        ),
    ]
