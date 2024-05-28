# Generated by Django 5.0.3 on 2024-05-28 20:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0060_churchmoderation_address_churchmoderation_city_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='churchmoderation',
            name='category',
            field=models.CharField(choices=[('loc_null', 'Location Null'), ('loc_api', 'Location From Api'), ('name_differs', 'Name Differs'), ('parish_differs', 'Parish Differs'), ('location_differs', 'Location Differs'), ('added_church', 'Added Church'), ('deleted_church', 'Deleted Church')], max_length=16),
        ),
        migrations.AlterField(
            model_name='parishmoderation',
            name='category',
            field=models.CharField(choices=[('name_differs', 'Name Differs'), ('website_differs', 'Website Differs'), ('added_parish', 'Added Parish'), ('deleted_parish', 'Deleted Parish')], max_length=16),
        ),
        migrations.AlterField(
            model_name='parishmoderation',
            name='name',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
