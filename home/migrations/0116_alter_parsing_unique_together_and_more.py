# Generated by Django 5.0.9 on 2024-10-13 09:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0115_alter_historicalschedule_exclude_periods_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='parsing',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='historicalparsing',
            name='current_year',
            field=models.SmallIntegerField(default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalparsing',
            name='truncated_html',
            field=models.TextField(default=None, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalparsing',
            name='truncated_html_hash',
            field=models.CharField(default=None, editable=False, max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='parsing',
            name='current_year',
            field=models.SmallIntegerField(default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='parsing',
            name='truncated_html',
            field=models.TextField(default=None, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='parsing',
            name='truncated_html_hash',
            field=models.CharField(default=None, editable=False, max_length=32),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='historicalparsing',
            name='church_desc_by_id',
            field=models.JSONField(editable=False),
        ),
        migrations.AlterField(
            model_name='parsing',
            name='church_desc_by_id',
            field=models.JSONField(editable=False),
        ),
        migrations.AlterField(
            model_name='parsing',
            name='pruning',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parsings', to='home.pruning'),
        ),
        migrations.AlterField(
            model_name='parsing',
            name='website',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parsings', to='home.website'),
        ),
        migrations.AlterUniqueTogether(
            name='parsing',
            unique_together={('truncated_html_hash', 'church_desc_by_id')},
        ),
    ]
