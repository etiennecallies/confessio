# Generated by Django 5.0.10 on 2024-12-11 17:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0012_remove_historicalregularschedule_history_user_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalparsingmoderation',
            name='validated_schedules_list',
        ),
        migrations.RemoveField(
            model_name='parsingmoderation',
            name='validated_schedules_list',
        ),
    ]