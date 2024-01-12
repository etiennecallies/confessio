# Generated by Django 4.2 on 2023-04-18 05:55

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Church',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('address', models.CharField(max_length=100)),
                ('zipcode', models.CharField(max_length=5)),
                ('city', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Parish',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('home_url', models.URLField()),
                ('confession_hours_url', models.URLField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
