# Generated by Django 5.0.9 on 2024-10-30 07:32

import django.db.models.deletion
import home.models.custom_fields
import simple_history.models
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0118_alter_parsing_unique_together_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='schedule',
            name='parsing',
        ),
        migrations.CreateModel(
            name='HistoricalOneOffSchedule',
            fields=[
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('church_id', models.SmallIntegerField(blank=True, null=True)),
                ('is_exception_rule', models.BooleanField()),
                ('duration_in_minutes', models.SmallIntegerField(blank=True, null=True)),
                ('start_isoformat', models.CharField(max_length=19)),
                ('weekday', models.SmallIntegerField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('parsing', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='home.parsing')),
            ],
            options={
                'verbose_name': 'historical one off schedule',
                'verbose_name_plural': 'historical one off schedules',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalRegularSchedule',
            fields=[
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('church_id', models.SmallIntegerField(blank=True, null=True)),
                ('is_exception_rule', models.BooleanField()),
                ('duration_in_minutes', models.SmallIntegerField(blank=True, null=True)),
                ('rrule', models.TextField()),
                ('include_periods', home.models.custom_fields.ChoiceArrayField(base_field=models.CharField(choices=[('january', 'JANUARY'), ('february', 'FEBRUARY'), ('march', 'MARCH'), ('april', 'APRIL'), ('may', 'MAY'), ('june', 'JUNE'), ('july', 'JULY'), ('august', 'AUGUST'), ('september', 'SEPTEMBER'), ('october', 'OCTOBER'), ('november', 'NOVEMBER'), ('december', 'DECEMBER'), ('advent', 'ADVENT'), ('lent', 'LENT'), ('school_holidays', 'SCHOOL_HOLIDAYS')], max_length=16), blank=True, size=None)),
                ('exclude_periods', home.models.custom_fields.ChoiceArrayField(base_field=models.CharField(choices=[('january', 'JANUARY'), ('february', 'FEBRUARY'), ('march', 'MARCH'), ('april', 'APRIL'), ('may', 'MAY'), ('june', 'JUNE'), ('july', 'JULY'), ('august', 'AUGUST'), ('september', 'SEPTEMBER'), ('october', 'OCTOBER'), ('november', 'NOVEMBER'), ('december', 'DECEMBER'), ('advent', 'ADVENT'), ('lent', 'LENT'), ('school_holidays', 'SCHOOL_HOLIDAYS')], max_length=16), blank=True, size=None)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('parsing', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='home.parsing')),
            ],
            options={
                'verbose_name': 'historical regular schedule',
                'verbose_name_plural': 'historical regular schedules',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='OneOffSchedule',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('church_id', models.SmallIntegerField(blank=True, null=True)),
                ('is_exception_rule', models.BooleanField()),
                ('duration_in_minutes', models.SmallIntegerField(blank=True, null=True)),
                ('start_isoformat', models.CharField(max_length=19)),
                ('weekday', models.SmallIntegerField(blank=True, null=True)),
                ('parsing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='one_off_schedules', to='home.parsing')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RegularSchedule',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('church_id', models.SmallIntegerField(blank=True, null=True)),
                ('is_exception_rule', models.BooleanField()),
                ('duration_in_minutes', models.SmallIntegerField(blank=True, null=True)),
                ('rrule', models.TextField()),
                ('include_periods', home.models.custom_fields.ChoiceArrayField(base_field=models.CharField(choices=[('january', 'JANUARY'), ('february', 'FEBRUARY'), ('march', 'MARCH'), ('april', 'APRIL'), ('may', 'MAY'), ('june', 'JUNE'), ('july', 'JULY'), ('august', 'AUGUST'), ('september', 'SEPTEMBER'), ('october', 'OCTOBER'), ('november', 'NOVEMBER'), ('december', 'DECEMBER'), ('advent', 'ADVENT'), ('lent', 'LENT'), ('school_holidays', 'SCHOOL_HOLIDAYS')], max_length=16), blank=True, size=None)),
                ('exclude_periods', home.models.custom_fields.ChoiceArrayField(base_field=models.CharField(choices=[('january', 'JANUARY'), ('february', 'FEBRUARY'), ('march', 'MARCH'), ('april', 'APRIL'), ('may', 'MAY'), ('june', 'JUNE'), ('july', 'JULY'), ('august', 'AUGUST'), ('september', 'SEPTEMBER'), ('october', 'OCTOBER'), ('november', 'NOVEMBER'), ('december', 'DECEMBER'), ('advent', 'ADVENT'), ('lent', 'LENT'), ('school_holidays', 'SCHOOL_HOLIDAYS')], max_length=16), blank=True, size=None)),
                ('parsing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='regular_schedules', to='home.parsing')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.DeleteModel(
            name='HistoricalSchedule',
        ),
        migrations.DeleteModel(
            name='Schedule',
        ),
    ]
