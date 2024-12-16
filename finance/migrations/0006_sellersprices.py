# Generated by Django 5.1.2 on 2024-12-16 14:30

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0005_remove_botpayment_action_id_botpayment_info'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SellersPrices',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usage_limit', models.PositiveIntegerField()),
                ('expire_limit', models.PositiveIntegerField()),
                ('price', models.PositiveIntegerField()),
                ('user_limit', models.PositiveIntegerField(default=0)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
