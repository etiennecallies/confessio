# Generated by Django 5.0.3 on 2024-06-07 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0061_alter_churchmoderation_category_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='church',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
