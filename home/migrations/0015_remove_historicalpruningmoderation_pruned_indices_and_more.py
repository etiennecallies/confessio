# Generated by Django 5.0.10 on 2024-12-11 18:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0014_historicalpruning_human_indices_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalpruningmoderation',
            name='pruned_indices',
        ),
        migrations.RemoveField(
            model_name='pruningmoderation',
            name='pruned_indices',
        ),
    ]