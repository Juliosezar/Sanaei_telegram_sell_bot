# Generated by Django 5.1.2 on 2025-01-07 19:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0003_sendmessage'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sendmessage',
            name='message',
        ),
        migrations.AddField(
            model_name='sendmessage',
            name='message_id',
            field=models.IntegerField(default=-1),
        ),
    ]
