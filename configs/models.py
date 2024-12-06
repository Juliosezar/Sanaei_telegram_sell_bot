from django.db import models
from customers.models import Customer
from servers.models import Server


class Service(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True)
    uuid = models.UUIDField(unique=True)
    name = models.CharField(max_length=50, unique=True)
    usage_limit = models.IntegerField(default=0)
    expire_time = models.BigIntegerField(default=0)
    user_limit = models.SmallIntegerField(default=0)
    paid = models.BooleanField(default=True)
    status = models.SmallIntegerField(default=0) # -1 creating / 0 Active / 1 disable / 2 Ended / 4 deleting


class Config(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    status = models.SmallIntegerField(default=0) # 0 => active / 1 => disable / 2 => deleted
    usage = models.BigIntegerField(default=0)
    last_update = models.BigIntegerField(default=0)
