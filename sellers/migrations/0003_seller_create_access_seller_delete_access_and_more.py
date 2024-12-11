# Generated by Django 5.1.2 on 2024-12-10 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sellers', '0002_seller_bot'),
    ]

    operations = [
        migrations.AddField(
            model_name='seller',
            name='create_access',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='seller',
            name='delete_access',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='seller',
            name='finance_access',
            field=models.BooleanField(default=False),
        ),
    ]
