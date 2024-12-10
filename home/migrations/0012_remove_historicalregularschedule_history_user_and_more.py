# Generated by Django 5.0.10 on 2024-12-10 23:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0011_rename_error_detail_historicalparsing_llm_error_detail_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalregularschedule',
            name='history_user',
        ),
        migrations.RemoveField(
            model_name='historicalregularschedule',
            name='parsing',
        ),
        migrations.RemoveField(
            model_name='oneoffschedule',
            name='parsing',
        ),
        migrations.RemoveField(
            model_name='regularschedule',
            name='parsing',
        ),
        migrations.RemoveField(
            model_name='historicalparsing',
            name='is_related_to_adoration',
        ),
        migrations.RemoveField(
            model_name='historicalparsing',
            name='is_related_to_mass',
        ),
        migrations.RemoveField(
            model_name='historicalparsing',
            name='is_related_to_permanence',
        ),
        migrations.RemoveField(
            model_name='historicalparsing',
            name='possible_by_appointment',
        ),
        migrations.RemoveField(
            model_name='historicalparsing',
            name='will_be_seasonal_events',
        ),
        migrations.RemoveField(
            model_name='parsing',
            name='is_related_to_adoration',
        ),
        migrations.RemoveField(
            model_name='parsing',
            name='is_related_to_mass',
        ),
        migrations.RemoveField(
            model_name='parsing',
            name='is_related_to_permanence',
        ),
        migrations.RemoveField(
            model_name='parsing',
            name='possible_by_appointment',
        ),
        migrations.RemoveField(
            model_name='parsing',
            name='will_be_seasonal_events',
        ),
        migrations.DeleteModel(
            name='HistoricalOneOffSchedule',
        ),
        migrations.DeleteModel(
            name='HistoricalRegularSchedule',
        ),
        migrations.DeleteModel(
            name='OneOffSchedule',
        ),
        migrations.DeleteModel(
            name='RegularSchedule',
        ),
    ]
