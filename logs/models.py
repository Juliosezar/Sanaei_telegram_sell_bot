from django.db import models
from accounts.models import User
from configs.models import Service
from customers.models import Customer


class CeleryLog(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    description = models.TextField()
    timestamp = models.PositiveBigIntegerField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True)


class CustomerLog(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True)
    description = models.TextField()
    timestamp = models.PositiveBigIntegerField()


class ServiceLog(models.Model):
    sevice = models.ForeignKey(Service, on_delete=models.CASCADE, null=True)
    description = models.TextField()
    timestamp = models.PositiveBigIntegerField()