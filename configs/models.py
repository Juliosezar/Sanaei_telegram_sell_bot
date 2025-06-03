from django.db import models
from accounts.models import User
from customers.models import Customer
from servers.models import Server

class Service(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True)
    uuid = models.UUIDField(unique=True)
    name = models.CharField(max_length=50, unique=True)
    usage_limit = models.IntegerField(default=0)
    usage = models.FloatField(default=0)
    expire_time = models.BigIntegerField(default=0)
    start_time = models.BigIntegerField(default=0)
    user_limit = models.SmallIntegerField(default=0)
    paid = models.BooleanField(default=True)
    status = models.SmallIntegerField(default=0, choices=[(0,'Active'), (1,'disable'), (2,'Ended'), (4,'deleting')])
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True) # null => main bot
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, related_name='created_by')
    price = models.PositiveBigIntegerField(null=True)
    infinit_limit = models.PositiveIntegerField(null=True, default=0)


class Config(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    status = models.SmallIntegerField(default=-1, choices=[(-1,'not_created'),(1,'active'),(2,'disable'),(3,'deleted')])
    usage = models.FloatField(default=0)
    last_update = models.BigIntegerField(default=0)


class ConfigJobsQueue(models.Model):
    config = models.ForeignKey(Config, on_delete=models.CASCADE)
    job = models.IntegerField(choices=[(0, "create"), (1, "disable"), (2, "delete"), (3, "enable"), (4, "reset")])
    done = models.BooleanField(default=False)
    last_try = models.BigIntegerField(default=0)
    try_count = models.SmallIntegerField(default=0)
    by_user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, related_name='by_user')


class EndNotif(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    timestamp = models.PositiveBigIntegerField()
    type = models.SmallIntegerField(choices=[(0,"ended"),(1,"time"),(2,"usage")])
