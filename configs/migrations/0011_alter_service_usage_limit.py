# Generated by Django 5.1.2 on 2024-12-15 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configs', '0010_service_created_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='usage_limit',
            field=models.IntegerField(default=0),
        ),
    ]