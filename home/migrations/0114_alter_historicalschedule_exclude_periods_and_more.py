# Generated by Django 5.0.8 on 2024-10-04 11:35

import home.models.custom_fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0113_alter_historicalschedule_church_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalschedule',
            name='exclude_periods',
            field=home.models.custom_fields.ChoiceArrayField(base_field=models.CharField(choices=[('january', 'JANUARY'), ('february', 'FEBRUARY'), ('march', 'MARCH'), ('april', 'APRIL'), ('may', 'MAY'), ('june', 'JUNE'), ('july', 'JULY'), ('august', 'AUGUST'), ('september', 'SEPTEMBER'), ('october', 'OCTOBER'), ('november', 'NOVEMBER'), ('december', 'DECEMBER'), ('advent', 'ADVENT'), ('lent', 'LENT'), ('school_holidays', 'SCHOOL_HOLIDAYS')], max_length=16), size=None),
        ),
        migrations.AlterField(
            model_name='historicalschedule',
            name='include_periods',
            field=home.models.custom_fields.ChoiceArrayField(base_field=models.CharField(choices=[('january', 'JANUARY'), ('february', 'FEBRUARY'), ('march', 'MARCH'), ('april', 'APRIL'), ('may', 'MAY'), ('june', 'JUNE'), ('july', 'JULY'), ('august', 'AUGUST'), ('september', 'SEPTEMBER'), ('october', 'OCTOBER'), ('november', 'NOVEMBER'), ('december', 'DECEMBER'), ('advent', 'ADVENT'), ('lent', 'LENT'), ('school_holidays', 'SCHOOL_HOLIDAYS')], max_length=16), size=None),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='exclude_periods',
            field=home.models.custom_fields.ChoiceArrayField(base_field=models.CharField(choices=[('january', 'JANUARY'), ('february', 'FEBRUARY'), ('march', 'MARCH'), ('april', 'APRIL'), ('may', 'MAY'), ('june', 'JUNE'), ('july', 'JULY'), ('august', 'AUGUST'), ('september', 'SEPTEMBER'), ('october', 'OCTOBER'), ('november', 'NOVEMBER'), ('december', 'DECEMBER'), ('advent', 'ADVENT'), ('lent', 'LENT'), ('school_holidays', 'SCHOOL_HOLIDAYS')], max_length=16), size=None),
        ),
        migrations.AlterField(
            model_name='schedule',
            name='include_periods',
            field=home.models.custom_fields.ChoiceArrayField(base_field=models.CharField(choices=[('january', 'JANUARY'), ('february', 'FEBRUARY'), ('march', 'MARCH'), ('april', 'APRIL'), ('may', 'MAY'), ('june', 'JUNE'), ('july', 'JULY'), ('august', 'AUGUST'), ('september', 'SEPTEMBER'), ('october', 'OCTOBER'), ('november', 'NOVEMBER'), ('december', 'DECEMBER'), ('advent', 'ADVENT'), ('lent', 'LENT'), ('school_holidays', 'SCHOOL_HOLIDAYS')], max_length=16), size=None),
        ),
    ]