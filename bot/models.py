from django.db import models
from customers.models import Customer



class CustomerTmpStatus(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, default="normal")
    values = models.JSONField(default=dict)


class SellerBots(models.Model):
    name = models.CharField(max_length=30)


class SendMessage(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    message = models.TextField()
    done = models.BooleanField(default=False)
    created_at = models.BigIntegerField()
    updated_at = models.BigIntegerField()
    try_count = models.IntegerField(default=0)

    def __str__(self):
        return str(self.done )+ " / " + self.message[:40]


