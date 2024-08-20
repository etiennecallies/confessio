# Generated by Django 5.0.8 on 2024-08-20 14:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0092_page_last_validated_at_page_validation_counter_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalwebsitemoderation',
            name='category',
            field=models.CharField(choices=[('name_concat', 'Name Concatenated'), ('name_websit', 'Name Website Title'), ('hu_no_resp', 'Home Url No Response'), ('hu_no_conf', 'Home Url No Confession'), ('hu_conflict', 'Home Url Conflict'), ('hu_too_long', 'Home Url Too Long')], max_length=11),
        ),
        migrations.AlterField(
            model_name='websitemoderation',
            name='category',
            field=models.CharField(choices=[('name_concat', 'Name Concatenated'), ('name_websit', 'Name Website Title'), ('hu_no_resp', 'Home Url No Response'), ('hu_no_conf', 'Home Url No Confession'), ('hu_conflict', 'Home Url Conflict'), ('hu_too_long', 'Home Url Too Long')], max_length=11),
        ),
    ]
