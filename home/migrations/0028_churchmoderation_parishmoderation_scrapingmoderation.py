# Generated by Django 5.0.1 on 2024-02-24 15:24

import django.contrib.gis.db.models.fields
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0027_sentence_scraping_sentence_updated_by'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChurchModeration',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('validated_at', models.DateTimeField(null=True)),
                ('category', models.CharField(choices=[('loc_null', 'Location Null')], max_length=8)),
                ('location', django.contrib.gis.db.models.fields.PointField(geography=True, srid=4326)),
                ('church', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='moderations', to='home.church')),
                ('validated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('church', 'category')},
            },
        ),
        migrations.CreateModel(
            name='ParishModeration',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('validated_at', models.DateTimeField(null=True)),
                ('category', models.CharField(choices=[('name_concat', 'Name Concatenated'), ('name_websit', 'Name Website Title'), ('hu_no_resp', 'Home Url No Response'), ('hu_no_conf', 'Home Url No Confession')], max_length=11)),
                ('name', models.CharField(max_length=300)),
                ('home_url', models.URLField()),
                ('parish', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='moderations', to='home.parish')),
                ('validated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('parish', 'category')},
            },
        ),
        migrations.CreateModel(
            name='ScrapingModeration',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('validated_at', models.DateTimeField(null=True)),
                ('category', models.CharField(choices=[('chp_new', 'Confession Html Pruned New')], max_length=7)),
                ('confession_html_pruned', models.TextField()),
                ('scraping', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='moderations', to='home.scraping')),
                ('validated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('scraping', 'category')},
            },
        ),
    ]