# Generated by Django 4.2 on 2023-05-25 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0010_alter_parish_home_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='church',
            name='messesinfo_id',
            field=models.CharField(max_length=100, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='parish',
            name='messesinfo_community_id',
            field=models.CharField(max_length=100, null=True, unique=True),
        ),
    ]
