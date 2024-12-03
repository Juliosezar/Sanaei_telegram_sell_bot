from django.db import models

class Customer(models.Model):
    chat_id = models.IntegerField(unique=True, primary_key=True)
    name = models.CharField(max_length=50)
    username = models.CharField(max_length=50)
    wallet = models.IntegerField(default=0)
    purchase_number = models.PositiveIntegerField(default=0)
    test_config = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    banned = models.BooleanField(default=False)
