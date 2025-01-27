# Generated by Django 5.0.11 on 2025-01-27 12:30

import django.db.models.deletion
import simple_history.models
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0019_report_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalReportModeration',
            fields=[
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('validated_at', models.DateTimeField(null=True)),
                ('marked_as_bug_at', models.DateTimeField(null=True)),
                ('bug_description', models.CharField(default=None, max_length=200, null=True)),
                ('category', models.CharField(choices=[('good', 'Good'), ('outdated', 'Outdated'), ('error', 'Error')], max_length=16)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('marked_as_bug_by', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('report', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='home.report')),
                ('validated_by', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical report moderation',
                'verbose_name_plural': 'historical report moderations',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='ReportModeration',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('validated_at', models.DateTimeField(null=True)),
                ('marked_as_bug_at', models.DateTimeField(null=True)),
                ('bug_description', models.CharField(default=None, max_length=200, null=True)),
                ('category', models.CharField(choices=[('good', 'Good'), ('outdated', 'Outdated'), ('error', 'Error')], max_length=16)),
                ('marked_as_bug_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='report_marked_as_bug_by', to=settings.AUTH_USER_MODEL)),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='moderations', to='home.report')),
                ('validated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='report_validated_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('report', 'category')},
            },
        ),
    ]
