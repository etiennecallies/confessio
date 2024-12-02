# Generated by Django 5.0.9 on 2024-12-02 13:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_alter_scraping_page'),
    ]

    operations = [
        migrations.RenameField(
            model_name='scraping',
            old_name='page',
            new_name='temp_page',
        ),
        migrations.AddField(
            model_name='historicalpage',
            name='scraping',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='home.scraping'),
        ),
        migrations.AddField(
            model_name='page',
            name='scraping',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='page', to='home.scraping'),
        ),
    ]
