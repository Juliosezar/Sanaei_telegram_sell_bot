# Generated by Django 5.1.2 on 2024-12-19 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_bot'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='disable_config_acc',
            field=models.BooleanField(default=False),
        ),
    ]
