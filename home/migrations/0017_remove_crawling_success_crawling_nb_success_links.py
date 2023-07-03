# Generated by Django 4.2 on 2023-07-03 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0016_scraping_confession_html_refined'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='crawling',
            name='success',
        ),
        migrations.AddField(
            model_name='crawling',
            name='nb_success_links',
            field=models.PositiveSmallIntegerField(default=0),
            preserve_default=False,
        ),
    ]
