# Generated by Django 5.0.10 on 2024-12-10 23:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0010_historicalparsing_human_json_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='historicalparsing',
            old_name='error_detail',
            new_name='llm_error_detail',
        ),
        migrations.RenameField(
            model_name='parsing',
            old_name='error_detail',
            new_name='llm_error_detail',
        ),
    ]
