# Generated by Django 5.0.9 on 2024-11-01 22:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0121_rename_is_exception_rule_historicaloneoffschedule_is_cancellation_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalpage',
            name='parsing_last_validated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalpage',
            name='parsing_validation_counter',
            field=models.SmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='historicalwebsite',
            name='parsing_last_validated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalwebsite',
            name='parsing_validation_counter',
            field=models.SmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='page',
            name='parsing_last_validated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='parsing_validation_counter',
            field=models.SmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='website',
            name='parsing_last_validated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='website',
            name='parsing_validation_counter',
            field=models.SmallIntegerField(default=0),
        ),
    ]
