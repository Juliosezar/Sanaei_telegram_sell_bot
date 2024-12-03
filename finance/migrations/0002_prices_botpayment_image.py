# Generated by Django 5.1.2 on 2024-12-02 19:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Prices',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usage_limit', models.PositiveIntegerField()),
                ('expire_limit', models.PositiveIntegerField()),
                ('price', models.PositiveIntegerField()),
                ('user_limit', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.AddField(
            model_name='botpayment',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='payment_images/'),
        ),
    ]
