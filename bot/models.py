from django.db import models
from customers.models import Customer

class CustomerTmpStatus(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, default="normal")
    values = models.JSONField(default=dict)