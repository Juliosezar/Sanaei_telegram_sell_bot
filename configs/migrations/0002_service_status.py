# Generated by Django 5.1.2 on 2024-12-05 17:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='status',
            field=models.SmallIntegerField(default=0),
        ),
    ]
