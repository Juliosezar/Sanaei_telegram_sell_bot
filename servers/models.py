from django.db import models
from django.db.models import PositiveIntegerField


class Server(models.Model):
    ID = models.PositiveSmallIntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    url = models.URLField()
    fake_domain = models.CharField(max_length=50)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    inbound_id = models.PositiveSmallIntegerField()
    inbound_port = models.PositiveIntegerField()
    active = models.BooleanField(default=True)
    maximum_connection = PositiveIntegerField(default=0)
    last_update = models.BigIntegerField(default=0)


